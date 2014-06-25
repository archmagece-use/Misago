from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
from misago.core import forms, threadstore
from misago.core.validators import validate_sluggable
from misago.acl.models import Role
from misago.users.models import Rank
from misago.users.validators import (validate_username, validate_email,
                                     validate_password)


"""
Users forms
"""
class UserBaseForm(forms.ModelForm):
    username = forms.CharField(
        label=_("Username"))
    title = forms.CharField(
        label=_("Custom title"),
        required=False)
    email = forms.EmailField(
        label=_("E-mail address"))

    class Meta:
        model = get_user_model()
        fields = ['username', 'email', 'title']

    def clean_username(self):
        data = self.cleaned_data['username']
        validate_username(data)
        return data

    def clean_email(self):
        data = self.cleaned_data['email']
        validate_email(data)
        return data

    def clean_new_password(self):
        data = self.cleaned_data['new_password']
        validate_password(data)
        return data

    def clean_roles(self):
        data = self.cleaned_data['roles']

        for role in data:
            if role.special_role == 'authenticated':
                break
        else:
            message = _('All registered members must have "Member" role.')
            raise forms.ValidationError(message)

        return data


class NewUserForm(UserBaseForm):
    new_password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput)

    class Meta:
        model = get_user_model()
        fields = ['username', 'email', 'title']


class EditUserForm(forms.ModelForm):
    new_password = forms.CharField(
        label=_("Change password to"),
        widget=forms.PasswordInput,
        required=False)

    class Meta:
        model = get_user_model()
        fields = ['username', 'email', 'title']


def UserFormFactory(FormType, instance):
    extra_fields = {}

    ranks = Rank.objects.order_by('name')
    if ranks.exists():
        extra_fields['rank'] = forms.ModelChoiceField(
            label=_("Rank"),
            help_text=_("Ranks are used to group and distinguish users. "
                        "They are also used to add permissions to groups of "
                        "users."),
            queryset=ranks,
            initial=instance.rank,
            required=False,
            empty_label=_("No rank"))

    roles = Role.objects.order_by('name')
    extra_fields['roles'] = forms.ModelMultipleChoiceField(
        label=_("Roles"),
        help_text=_("Individual roles of this user."),
        queryset=roles,
        initial=instance.roles.all() if instance.pk else None,
        widget=forms.CheckboxSelectMultiple)

    return type('UserFormFinal', (FormType,), extra_fields)


import warnings
warnings.warn("Admin search inactive users not implemented yet.",
              FutureWarning)


def StaffFlagUserFormFactory(FormType, instance, add_staff_field):
    FormType = UserFormFactory(FormType, instance)

    if add_staff_field:
        staff_levels = (
            (0, _("No access")),
            (1, _("Administrator")),
            (2, _("Superadmin")),
        )

        staff_fields = {
            'staff_level': forms.TypedChoiceField(
                label=_("Admin level"),
                help_text=_('Only administrators can access admin sites. '
                            'In addition to admin site access, superadmins '
                            'can also change other members admin levels.'),
                coerce=int,
                choices=staff_levels,
                initial=instance.staff_level),
        }

        return type('StaffUserForm', (FormType,), staff_fields)
    else:
        return FormType


class SearchUsersFormBase(forms.Form):
    username = forms.CharField(label=_("Username starts with"), required=False)
    email = forms.CharField(label=_("E-mail starts with"), required=False)
    #rank = forms.TypedChoiceField(label=_("Rank"),
    #                              coerce=int,
    #                              required=False,
    #                              choices=ranks_list)
    #role = forms.TypedChoiceField(label=_("Role"),
    #                              coerce=int,
    #                              required=False,
    #                              choices=roles_list)
    inactive = forms.YesNoSwitch(label=_("Inactive only"))
    is_staff = forms.YesNoSwitch(label=_("Is administrator"))

    def filter_queryset(self, search_criteria, queryset):
        criteria = search_criteria
        if criteria.get('username'):
            queryset = queryset.filter(
                username_slug__startswith=criteria.get('username').lower())

        if criteria.get('email'):
            queryset = queryset.filter(
                email__istartswith=criteria.get('email'))

        if criteria.get('rank'):
            queryset = queryset.filter(
                rank_id=criteria.get('rank'))

        if criteria.get('role'):
            queryset = queryset.filter(
                roles__id=criteria.get('role'))

        if criteria.get('inactive'):
            pass


        if criteria.get('is_staff'):
            queryset = criteria.filter(is_staff=True)

        return queryset


def SearchUsersForm(*args, **kwargs):
    """
    Factory that uses cache for ranks and roles,
    and makes those ranks and roles typed choice fields that play nice
    with passing values via GET
    """
    ranks_choices = threadstore.get('misago_admin_ranks_choices', 'nada')
    if ranks_choices == 'nada':
        ranks_choices = [('', _("All ranks"))]
        for rank in Rank.objects.order_by('name').iterator():
            ranks_choices.append((rank.pk, rank.name))
        threadstore.set('misago_admin_ranks_choices', ranks_choices)

    roles_choices = threadstore.get('misago_admin_roles_choices', 'nada')
    if roles_choices == 'nada':
        roles_choices = [('', _("All roles"))]
        for role in Role.objects.order_by('name').iterator():
            roles_choices.append((role.pk, role.name))
        threadstore.set('misago_admin_roles_choices', roles_choices)


    extra_fields = {
        'rank': forms.TypedChoiceField(label=_("Has rank"),
                                       coerce=int,
                                       required=False,
                                       choices=ranks_choices),
        'role': forms.TypedChoiceField(label=_("Has role"),
                                       coerce=int,
                                       required=False,
                                       choices=roles_choices)
    }

    FinalForm =  type('SearchUsersFormFinal',
                      (SearchUsersFormBase,),
                      extra_fields)
    return FinalForm(*args, **kwargs)


"""
Ranks form
"""
class RankForm(forms.ModelForm):
    name = forms.CharField(
        label=_("Name"),
        validators=[validate_sluggable()],
        help_text=_('Short and descriptive name of all users with this rank. '
                    '"The Team" or "Game Masters" are good examples.'))
    title = forms.CharField(
        label=_("User title"), required=False,
        help_text=_('Optional, singular version of rank name displayed by '
                    'user names. For example "GM" or "Dev".'))
    description = forms.CharField(
        label=_("Description"), max_length=2048, required=False,
        widget=forms.Textarea(attrs={'rows': 3}),
        help_text=_("Optional description explaining function or status of "
                    "members distincted with this rank."))
    roles = forms.ModelMultipleChoiceField(
        label=_("User roles"), queryset=Role.objects.order_by('name'),
        required=False,  widget=forms.CheckboxSelectMultiple,
        help_text=_('Rank can give users with it additional roles.'))
    css_class = forms.CharField(
        label=_("CSS class"), required=False,
        help_text=_("Optional css class added to content belonging to this "
                    "rank owner."))
    is_tab = forms.BooleanField(
        label=_("Give rank dedicated tab on users list"), required=False,
        help_text=_("Selecting this option will make users with this rank "
                    "easily discoverable by others trough dedicated page on "
                    "forum users list."))
    is_on_index = forms.BooleanField(
        label=_("Show users online on forum index"), required=False,
        help_text=_("Selecting this option will make forum inform other "
                    "users of their availability by displaying them on forum "
                    "index page."))

    class Meta:
        model = Rank
        fields = [
            'name',
            'description',
            'css_class',
            'title',
            'roles',
            'is_tab',
            'is_on_index',
        ]

    def clean(self):
        data = super(RankForm, self).clean()

        self.instance.set_name(data.get('name'))
        return data
