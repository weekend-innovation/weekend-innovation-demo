from django.db import migrations, models


def normalize_deadline(apps, schema_editor):
    Challenge = apps.get_model('challenges', 'Challenge')
    qs = Challenge.objects.filter(
        deadline__isnull=False,
        evaluation_deadline__isnull=False,
    ).exclude(deadline=models.F('evaluation_deadline'))
    for challenge in qs.iterator():
        challenge.deadline = challenge.evaluation_deadline
        challenge.save(update_fields=['deadline'])


def noop_reverse(apps, schema_editor):
    # 旧deadlineは復元できないため no-op
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('challenges', '0003_populate_phase_deadlines'),
    ]

    operations = [
        migrations.RunPython(normalize_deadline, noop_reverse),
    ]
