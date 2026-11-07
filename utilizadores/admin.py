from django import forms
from django.contrib import admin
from django.contrib.auth.models import User
from django.db.models import Q

from .models import (
    Aluno,
    Staff,
    Perfil,
    PreferenciasUtilizador,
)


class ContaUtilizadorForm(forms.ModelForm):

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if len(email) > 150:
            raise forms.ValidationError(
                "O e-mail não pode ultrapassar 150 caracteres."
            )

        utilizador_id = getattr(self.instance, "utilizador_id", None)

        utilizadores = User.objects.filter(
            Q(username__iexact=email) | Q(email__iexact=email)
        )

        if utilizador_id:
            utilizadores = utilizadores.exclude(id=utilizador_id)

        if utilizadores.exists():
            raise forms.ValidationError(
                "Já existe uma conta de utilizador com este e-mail."
            )

        if Aluno.objects.filter(email__iexact=email).exclude(
            pk=self.instance.pk
        ).exists():
            raise forms.ValidationError(
                "Este e-mail já está associado a um Aluno."
            )

        if Staff.objects.filter(email__iexact=email).exclude(
            pk=self.instance.pk
        ).exists():
            raise forms.ValidationError(
                "Este e-mail já está associado a um Staff."
            )

        return email


class AlunoAdminForm(ContaUtilizadorForm):

    class Meta:
        model = Aluno
        fields = ("nome", "email", "curso")


class StaffAdminForm(ContaUtilizadorForm):

    class Meta:
        model = Staff
        fields = ("nome", "email")


class ContaAdminMixin:

    def save_model(self, request, obj, form, change):
        email = obj.email.strip().lower()

        if not obj.utilizador_id:
            utilizador = User(
                username=email,
                email=email,
                first_name=obj.nome,
            )
            utilizador.set_unusable_password()
            utilizador.save()

            obj.utilizador = utilizador

        else:
            utilizador = obj.utilizador
            utilizador.username = email
            utilizador.email = email
            utilizador.first_name = obj.nome

            utilizador.save(
                update_fields=[
                    "username",
                    "email",
                    "first_name",
                ]
            )

        super().save_model(request, obj, form, change)


@admin.register(Aluno)
class AlunoAdmin(ContaAdminMixin, admin.ModelAdmin):

    form = AlunoAdminForm

    list_display = (
        "nome",
        "email",
        "curso",
        "utilizador",
    )

    list_filter = (
        "curso",
    )

    search_fields = (
        "nome",
        "email",
        "utilizador__username",
    )

    ordering = (
        "nome",
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "utilizador",
            "curso",
        )


@admin.register(Staff)
class StaffAdmin(ContaAdminMixin, admin.ModelAdmin):

    form = StaffAdminForm

    list_display = (
        "nome",
        "email",
        "utilizador",
    )

    search_fields = (
        "nome",
        "email",
        "utilizador__username",
    )

    ordering = (
        "nome",
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "utilizador",
        )


@admin.register(PreferenciasUtilizador)
class PreferenciasUtilizadorAdmin(admin.ModelAdmin):

    list_display = (
        "utilizador",
        "idioma",
    )

    list_filter = (
        "idioma",
    )

    search_fields = (
        "utilizador__username",
        "utilizador__email",
    )


@admin.register(Perfil)
class PerfilLegadoAdmin(admin.ModelAdmin):

    list_display = (
        "nome_completo",
        "utilizador",
        "tipo",
        "curso",
    )

    readonly_fields = tuple(
        field.name for field in Perfil._meta.fields
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
