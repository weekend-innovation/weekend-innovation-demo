from django.db import migrations


ANONYMOUS_NAMES = [
    ("Lion", "animal"),
    ("Tiger", "animal"),
    ("Bear", "animal"),
    ("Wolf", "animal"),
    ("Fox", "animal"),
    ("Eagle", "animal"),
    ("Hawk", "animal"),
    ("Dolphin", "animal"),
    ("Whale", "animal"),
    ("Shark", "animal"),
    ("Falcon", "animal"),
    ("Panther", "animal"),
    ("Leopard", "animal"),
    ("Cheetah", "animal"),
    ("Otter", "animal"),
    ("Maple", "plant"),
    ("Oak", "plant"),
    ("Pine", "plant"),
    ("Cedar", "plant"),
    ("Willow", "plant"),
    ("Birch", "plant"),
    ("Ivy", "plant"),
    ("Rose", "plant"),
    ("Tulip", "plant"),
    ("Lily", "plant"),
    ("Lotus", "plant"),
    ("Sakura", "plant"),
    ("Moss", "plant"),
    ("Fern", "plant"),
    ("Bamboo", "plant"),
    ("Quartz", "inorganic"),
    ("Granite", "inorganic"),
    ("Marble", "inorganic"),
    ("Obsidian", "inorganic"),
    ("Jade", "inorganic"),
    ("Onyx", "inorganic"),
    ("Amber", "inorganic"),
    ("Pearl", "inorganic"),
    ("Coral", "inorganic"),
    ("Steel", "inorganic"),
    ("Silver", "inorganic"),
    ("Gold", "inorganic"),
    ("Platinum", "inorganic"),
    ("Crystal", "inorganic"),
    ("Cobalt", "inorganic"),
]


def seed_anonymous_names(apps, schema_editor):
    AnonymousName = apps.get_model("proposals", "AnonymousName")
    for name, category in ANONYMOUS_NAMES:
        AnonymousName.objects.get_or_create(
            name=name,
            defaults={"category": category},
        )


def noop_reverse(apps, schema_editor):
    # 既存運用データを巻き込んで削除しないよう、ロールバックでは何もしない
    return


class Migration(migrations.Migration):
    dependencies = [
        ("proposals", "0009_alter_proposalevaluation_evaluation_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_anonymous_names, noop_reverse),
    ]

