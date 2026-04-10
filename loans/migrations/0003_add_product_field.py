from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('loans', '0002_auto_20260306_1450'),
    ]

    operations = [
        migrations.AddField(
            model_name='creditcardlead',
            name='product',
            field=models.CharField(max_length=5, db_index=True, default='CARD'),
        ),
    ]





