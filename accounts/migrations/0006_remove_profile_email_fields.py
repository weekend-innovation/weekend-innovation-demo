from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_alter_user_email_required'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='contributorprofile',
            name='email',
        ),
        migrations.RemoveField(
            model_name='proposerprofile',
            name='email',
        ),
    ]
