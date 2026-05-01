from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("selections", "0005_alter_selection_required_count_max_300"),
    ]

    operations = [
        migrations.AlterField(
            model_name="selection",
            name="required_count",
            field=models.IntegerField(
                validators=[MinValueValidator(1), MaxValueValidator(700)],
                verbose_name="選出人数",
            ),
        ),
    ]
