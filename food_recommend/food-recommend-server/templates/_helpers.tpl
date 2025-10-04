{{- define "food-recommend-server.name" -}}
{{- .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "food-recommend-server.fullname" -}}
{{- printf "%s-%s" .Release.Name (include "food-recommend-server.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "food-recommend-server.labels" -}}
app.kubernetes.io/name: {{ include "food-recommend-server.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{- define "food-recommend-server.selectorLabels" -}}
app.kubernetes.io/name: {{ include "food-recommend-server.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

