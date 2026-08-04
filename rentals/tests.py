from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core import mail
from rentals.models import CarProfile

class RentalsSystemTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create a test user
        self.username = 'testdriver'
        self.password = 'SuperSecret123!'
        self.user = User.objects.create_user(
            username=self.username,
            email='testdriver@example.com',
            password=self.password
        )

    def test_pages_http_status(self):
        """Verify that basic pages return a 200 OK status code."""
        urls = ['home', 'about', 'contact', 'login', 'register']
        for url_name in urls:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 200)

    def test_profile_redirects_when_anonymous(self):
        """Verify that accessing the profile page redirects an unauthenticated user to login."""
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_car_profile_creation_and_links(self):
        """Verify CarProfile model properties, numbers clean-up, and relationships."""
        # Create a mock image file
        image_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        mock_image = SimpleUploadedFile(
            name='test_car.png',
            content=image_content,
            content_type='image/png'
        )

        # Create profile
        car_profile = CarProfile.objects.create(
            user=self.user,
            car_name='Tesla Model S',
            car_image=mock_image,
            car_details='Fast electric sedan, 100D dual motor, premium spec.',
            phone_number='+1 (555) 123-4567',
            whatsapp_number='+1 (555) 987-6543'
        )

        # Test relation
        self.assertEqual(self.user.car_profiles.first(), car_profile)
        self.assertEqual(str(car_profile), "testdriver's Tesla Model S")

        # Test link helpers cleaning logic
        self.assertEqual(car_profile.call_link, 'tel:+15551234567')
        self.assertEqual(car_profile.whatsapp_link, 'https://wa.me/15559876543')

    def test_homepage_lists_cars(self):
        """Verify that the homepage lists active car profiles."""
        # Setup: Create profile for test user
        CarProfile.objects.create(
            user=self.user,
            car_name='Ford Mustang GT',
            car_image=SimpleUploadedFile('mustang.jpg', b'fakeimg', content_type='image/jpeg'),
            car_details='V8 muscle car, 5.0L.',
            phone_number='1234567890',
            whatsapp_number='0987654321'
        )
        
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ford Mustang GT')
        self.assertContains(response, 'Hosted by <strong class="text-white">testdriver</strong>')
        self.assertContains(response, 'tel:1234567890')
        self.assertContains(response, 'https://wa.me/0987654321')

    def test_profile_edit_by_owner(self):
        """Verify that a logged-in user can edit their own car profile."""
        self.client.login(username=self.username, password=self.password)
        car_profile = CarProfile.objects.create(
            user=self.user,
            car_name='Tesla Model S',
            car_image=SimpleUploadedFile('test.jpg', b'fakeimg', content_type='image/jpeg'),
            car_details='Old details',
            phone_number='1112223333',
            whatsapp_number='4445556666'
        )
        response = self.client.post(reverse('edit_car', args=[car_profile.id]), {
            'car_name': 'Tesla Model S Plaid',
            'car_details': 'New extremely fast specifications.',
            'phone_number': '9999999999',
            'whatsapp_number': '8888888888'
        })
        self.assertRedirects(response, reverse('profile'))
        car_profile.refresh_from_db()
        self.assertEqual(car_profile.car_name, 'Tesla Model S Plaid')
        self.assertEqual(car_profile.car_details, 'New extremely fast specifications.')

    def test_profile_delete_by_owner(self):
        """Verify that a logged-in user can delete their own car profile."""
        self.client.login(username=self.username, password=self.password)
        CarProfile.objects.create(
            user=self.user,
            car_name='Audi R8',
            car_image=SimpleUploadedFile('test.jpg', b'fakeimg', content_type='image/jpeg'),
            car_details='Supercar',
            phone_number='1234567890',
            whatsapp_number='1234567890'
        )
        car_profile = CarProfile.objects.filter(user=self.user).first()
        self.assertTrue(CarProfile.objects.filter(user=self.user).exists())
        response = self.client.post(reverse('delete_car', args=[car_profile.id]))
        self.assertRedirects(response, reverse('profile'))
        self.assertFalse(CarProfile.objects.filter(user=self.user).exists())

    def test_profile_delete_unauthenticated_fails(self):
        """Verify that deleting profile fails for anonymous user and redirects to login."""
        response = self.client.post(reverse('delete_car', args=[999]))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_password_reset_full_flow(self):
        """Verify the complete password reset workflow from request to verify to confirm."""
        # 1. Request Reset
        response = self.client.get(reverse('password_reset_request'))
        self.assertEqual(response.status_code, 200)

        # POST with non-existent email
        response = self.client.post(reverse('password_reset_request'), {'email': 'nonexistent@example.com'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No user is registered with this email address.")

        # POST with correct email
        response = self.client.post(reverse('password_reset_request'), {'email': 'testdriver@example.com'})
        self.assertRedirects(response, reverse('password_reset_verify'))

        # Check that email was sent and OTP is in session
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("ApexDrive - Password Reset OTP", mail.outbox[0].subject)
        
        session = self.client.session
        otp = session.get('reset_otp')
        self.assertIsNotNone(otp)
        self.assertEqual(session.get('reset_email'), 'testdriver@example.com')

        # 2. Verify OTP
        # GET without session should redirect
        anonymous_client = Client()
        response = anonymous_client.get(reverse('password_reset_verify'))
        self.assertRedirects(response, reverse('password_reset_request'))

        # GET with session
        response = self.client.get(reverse('password_reset_verify'))
        self.assertEqual(response.status_code, 200)

        # POST with incorrect OTP
        response = self.client.post(reverse('password_reset_verify'), {'otp': '000000'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid OTP.")

        # POST with correct OTP
        response = self.client.post(reverse('password_reset_verify'), {'otp': otp})
        self.assertRedirects(response, reverse('password_reset_confirm'))
        self.assertTrue(self.client.session.get('reset_otp_verified'))

        # 3. Confirm Password Reset
        # GET without verified status should redirect
        response = anonymous_client.get(reverse('password_reset_confirm'))
        self.assertRedirects(response, reverse('password_reset_request'))

        # GET with verified status
        response = self.client.get(reverse('password_reset_confirm'))
        self.assertEqual(response.status_code, 200)

        # POST with non-matching passwords
        response = self.client.post(reverse('password_reset_confirm'), {
            'password': 'NewPassword123!',
            'confirm_password': 'DifferentPassword123!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Passwords do not match.")

        # POST with matching passwords
        response = self.client.post(reverse('password_reset_confirm'), {
            'password': 'NewPassword123!',
            'confirm_password': 'NewPassword123!'
        })
        self.assertRedirects(response, reverse('login'))

        # Verify that session is cleaned up
        self.assertNotIn('reset_otp', self.client.session)
        self.assertNotIn('reset_email', self.client.session)
        self.assertNotIn('reset_otp_verified', self.client.session)

        # Try to authenticate with the new password
        login_success = self.client.login(username=self.username, password='NewPassword123!')
        self.assertTrue(login_success)


