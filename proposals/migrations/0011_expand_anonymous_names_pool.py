from django.db import migrations


def expand_anonymous_names_pool(apps, schema_editor):
    AnonymousName = apps.get_model("proposals", "AnonymousName")

    extra_animals = [f"Animal{idx:03d}" for idx in range(1, 41)]
    extra_plants = [f"Plant{idx:03d}" for idx in range(1, 41)]
    extra_inorganic = [f"Inorganic{idx:03d}" for idx in range(1, 41)]

    for name in extra_animals:
        AnonymousName.objects.get_or_create(name=name, defaults={"category": "animal"})
    for name in extra_plants:
        AnonymousName.objects.get_or_create(name=name, defaults={"category": "plant"})
    for name in extra_inorganic:
        AnonymousName.objects.get_or_create(name=name, defaults={"category": "inorganic"})


def noop_reverse(apps, schema_editor):
    return


class Migration(migrations.Migration):
    dependencies = [
        ("proposals", "0010_seed_anonymous_names"),
    ]

    operations = [
        migrations.RunPython(expand_anonymous_names_pool, noop_reverse),
    ]

