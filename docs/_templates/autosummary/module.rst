{{ fullname | escape | underline}}

.. automodule:: {{ fullname }}

   {% block attributes %}
   {%- if all_attributes %}
   .. rubric:: {{ _('Module Attributes') }}

   .. autosummary::
   {% for item in all_attributes %}
      {{ item }}
   {%- endfor %}
   {% endif %}
   {%- endblock %}

   {%- block functions %}
   {%- if all_functions %}
   .. rubric:: {{ _('Functions') }}

   .. autosummary::
   {% for item in all_functions if item != '__annotate__' %}
      {{ item }}
   {%- endfor %}
   {% endif %}
   {%- endblock %}

   {%- block classes %}
   {%- if all_classes %}
   .. rubric:: {{ _('Classes') }}

   .. autosummary::
   {% for item in all_classes %}
      {{ item }}
   {%- endfor %}
   {% endif %}
   {%- endblock %}

   {%- block exceptions %}
   {%- if all_exceptions %}
   .. rubric:: {{ _('Exceptions') }}

   .. autosummary::
   {% for item in all_exceptions %}
      {{ item }}
   {%- endfor %}
   {% endif %}
   {%- endblock %}

{%- block modules %}
{%- if all_modules %}
.. rubric:: Modules

.. autosummary::
   :toctree:
   :recursive:
{% for item in all_modules %}
   {{ item }}
{%- endfor %}
{% endif %}
{%- endblock %}
