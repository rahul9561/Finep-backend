from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loans', '0001_initial'),
    ]

    operations = [

        migrations.AddField(
            model_name='creditcardlead',
            name='executive_status',
            field=models.CharField(max_length=50, null=True, blank=True, db_index=True),
        ),

        migrations.AddField(
            model_name='creditcardlead',
            name='executive_updated_date',
            field=models.DateTimeField(null=True, blank=True),
        ),

        migrations.AddField(
            model_name='creditcardlead',
            name='executive_remarks',
            field=models.TextField(null=True, blank=True),
        ),
    ]