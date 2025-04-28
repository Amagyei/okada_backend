from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        # Update this to match the last migration of the app.
        ('users', '0002_fix_empty_user_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='userverification',
            name='phone_number',
            field=models.CharField(max_length=15, null=True, blank=True),
        ),
    ]