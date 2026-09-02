from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('detector', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='predictionhistory',
            name='session_key',
            field=models.CharField(blank=True, db_index=True, default='', max_length=40),
        ),
    ]
