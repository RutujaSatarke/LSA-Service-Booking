import pytest
from rest_framework import status
from django.urls import reverse
from bookings.models import LSAProfile, Skill


@pytest.mark.django_db
class TestLSASearchAPI:
    def setup_method(self):
        self.url = reverse('bookings:lsa-search')

    def test_search_returns_active_lsas(self, api_client, active_lsa, inactive_lsa):
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["id"] == active_lsa.id

    def test_skill_filtering(self, api_client, active_lsa, speech_skill):
        # Create another LSA with Speech Therapy skill
        speech_lsa = LSAProfile.objects.create(
            full_name="Sarah Therapist",
            email="sarah.t@lsa.example.com",
            phone="+1555998877",
            hourly_rate=40.00,
            is_active=True
        )
        speech_lsa.skills.add(speech_skill)

        # Filter by Math
        response_math = api_client.get(f"{self.url}?skills=Math")
        assert response_math.status_code == status.HTTP_200_OK
        assert response_math.data["count"] == 1
        assert response_math.data["results"][0]["id"] == active_lsa.id

        # Filter by Speech Therapy
        response_speech = api_client.get(f"{self.url}?skills=Speech Therapy")
        assert response_speech.status_code == status.HTTP_200_OK
        assert response_speech.data["count"] == 1
        assert response_speech.data["results"][0]["id"] == speech_lsa.id

    def test_n_plus_one_query_optimization(self, api_client, django_assert_num_queries):
        # Create 10 active LSAs with multiple skills
        skills = [Skill.objects.create(name=f"Skill-{i}") for i in range(5)]
        for i in range(10):
            lsa = LSAProfile.objects.create(
                full_name=f"LSA-{i}",
                email=f"lsa{i}@example.com",
                phone=f"+100000{i}",
                hourly_rate=25.00,
                is_active=True
            )
            lsa.skills.set(skills)

        # Evaluating Queryset + prefetching skills should execute a fixed number of queries (2 queries)
        # Query 1: Fetch LSAProfile models
        # Query 2: Fetch M2M Skill models in batch (prefetch_related)
        with django_assert_num_queries(2):
            response = api_client.get(self.url)
            assert response.status_code == status.HTTP_200_OK
            # Force evaluation of prefetched skills for all results
            for result in response.data["results"]:
                _ = result["skills"]
