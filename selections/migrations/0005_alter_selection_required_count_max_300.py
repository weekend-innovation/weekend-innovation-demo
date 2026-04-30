from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("selections", "0004_alter_selection_required_count"),
    ]

    operations = [
        migrations.AlterField(
            model_name="selection",
            name="required_count",
            field=models.IntegerField(
                validators=[MinValueValidator(1), MaxValueValidator(300)],
                verbose_name="選出人数",
            ),
        ),
    ]

