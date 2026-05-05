from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('challenges', '0004_normalize_deadline_to_evaluation_deadline'),
    ]

    operations = [
        migrations.AddField(
            model_name='challenge',
            name='is_contributor_anonymous',
            field=models.BooleanField(default=False, verbose_name='投稿者を匿名表示'),
        ),
    ]

