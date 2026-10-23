from django.db import migrations, models


def copiar_precos_staff_para_visitante(apps, schema_editor):
    Ementa = apps.get_model("menu", "Ementa")
    Extra = apps.get_model("menu", "Extra")
    alias = schema_editor.connection.alias

    for ementa in Ementa.objects.using(alias).all().iterator():
        Ementa.objects.using(alias).filter(pk=ementa.pk).update(
            preco_base_visitante=ementa.preco_base_staff
        )

    for extra in Extra.objects.using(alias).all().iterator():
        Extra.objects.using(alias).filter(pk=extra.pk).update(
            preco_visitante=extra.preco_staff
        )


class Migration(migrations.Migration):

    dependencies = [
        ("menu", "0006_ementa_itemementa_extra_ementa_entrada_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="ementa",
            name="preco_base_visitante",
            field=models.DecimalField(
                decimal_places=2, default=0, max_digits=6
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="extra",
            name="preco_visitante",
            field=models.DecimalField(
                decimal_places=2, default=0, max_digits=6
            ),
            preserve_default=False,
        ),
        migrations.RunPython(
            copiar_precos_staff_para_visitante,
            migrations.RunPython.noop,
        ),
    ]
