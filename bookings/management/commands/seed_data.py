from decimal import Decimal
from datetime import date, time
from django.core.management.base import BaseCommand
from bookings.models import Parent, Skill, LSAProfile, BookingRequest, Payment



class Command(BaseCommand):
    help = 'Idempotent seed data generator for HabotConnect platform'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting seed data execution...'))

        # 1. Create Skills
        skills_data = [
            {'name': 'Math', 'description': 'Elementary and high school mathematics support'},
            {'name': 'Science', 'description': 'Physics, Chemistry, and Biology assistance'},
            {'name': 'Dyslexia Support', 'description': 'Specialized reading and phonics intervention'},
            {'name': 'ADHD Coaching', 'description': 'Behavioral and executive function coaching'},
            {'name': 'Speech Therapy', 'description': 'Articulation and speech pathology exercises'},
        ]
        created_skills = {}
        for skill_info in skills_data:
            skill, created = Skill.objects.get_or_create(
                name=skill_info['name'],
                defaults={'description': skill_info['description']}
            )
            created_skills[skill.name] = skill
            status_str = 'Created' if created else 'Already exists'
            self.stdout.write(f"  Skill '{skill.name}': {status_str}")

        # 2. Create Parents
        parents_data = [
            {'full_name': 'Sarah Jenkins', 'email': 'sarah.j@example.com', 'phone': '+15550192834'},
            {'full_name': 'Michael Chen', 'email': 'mchen@example.com', 'phone': '+15550192835'},
            {'full_name': 'Emily Rodriguez', 'email': 'emily.r@example.com', 'phone': '+15550192836'},
        ]
        created_parents = []
        for p_info in parents_data:
            parent, created = Parent.objects.get_or_create(
                email=p_info['email'],
                defaults={'full_name': p_info['full_name'], 'phone': p_info['phone']}
            )
            created_parents.append(parent)
            status_str = 'Created' if created else 'Already exists'
            self.stdout.write(f"  Parent '{parent.full_name}': {status_str}")

        # 3. Create LSAs
        lsas_data = [
            {
                'full_name': 'John Doe',
                'email': 'john.doe@lsa.example.com',
                'phone': '+15550192901',
                'bio': 'Certified STEM tutor with 5 years experience in supporting children with dyslexia.',
                'hourly_rate': Decimal('25.00'),
                'is_active': True,
                'skills': ['Math', 'Science', 'Dyslexia Support']
            },
            {
                'full_name': 'Alice Smith',
                'email': 'alice.smith@lsa.example.com',
                'phone': '+15550192902',
                'bio': 'Special education specialist focusing on ADHD coaching and behavioral therapy.',
                'hourly_rate': Decimal('35.00'),
                'is_active': True,
                'skills': ['ADHD Coaching', 'Speech Therapy']
            },
            {
                'full_name': 'Robert Taylor',
                'email': 'robert.taylor@lsa.example.com',
                'phone': '+15550192903',
                'bio': 'High school math mentor and dyslexia specialist.',
                'hourly_rate': Decimal('30.00'),
                'is_active': False,  # Inactive LSA for testing filtering
                'skills': ['Math', 'Dyslexia Support']
            },
        ]
        created_lsas = []
        for lsa_info in lsas_data:
            lsa, created = LSAProfile.objects.get_or_create(
                email=lsa_info['email'],
                defaults={
                    'full_name': lsa_info['full_name'],
                    'phone': lsa_info['phone'],
                    'bio': lsa_info['bio'],
                    'hourly_rate': lsa_info['hourly_rate'],
                    'is_active': lsa_info['is_active'],
                }
            )
            # Associate skills
            skill_objs = [created_skills[sname] for sname in lsa_info['skills'] if sname in created_skills]
            lsa.skills.set(skill_objs)
            created_lsas.append(lsa)
            status_str = 'Created' if created else 'Already exists'
            self.stdout.write(f"  LSA '{lsa.full_name}': {status_str}")

        # 4. Create Sample Booking
        booking, created = BookingRequest.objects.get_or_create(
            parent=created_parents[0],
            lsa=created_lsas[0],
            session_date=date(2026, 8, 15),
            start_time=time(10, 0, 0),
            end_time=time(11, 0, 0),
            defaults={
                'status': BookingRequest.Status.CONFIRMED,
                'notes': 'Mathematics and dyslexia reading session.'
            }
        )
        status_str = 'Created' if created else 'Already exists'
        self.stdout.write(f"  Booking #{booking.id}: {status_str}")

        # 5. Create Sample Payment
        payment, pay_created = Payment.objects.get_or_create(
            transaction_id=f"TXN-SEED-{booking.id}",
            defaults={
                'booking': booking,
                'amount': created_lsas[0].hourly_rate,
                'currency': 'USD',
                'status': Payment.Status.SUCCESS,
                'provider': 'MockPay',
                'raw_response': {'success': True, 'message': 'Seeded transaction'}
            }
        )
        pay_status_str = 'Created' if pay_created else 'Already exists'
        self.stdout.write(f"  Payment #{payment.id} for Booking #{booking.id}: {pay_status_str}")

        self.stdout.write(self.style.SUCCESS('Seed data command completed successfully!'))
