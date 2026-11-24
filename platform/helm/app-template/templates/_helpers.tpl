{{- define "app-template.name" -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}