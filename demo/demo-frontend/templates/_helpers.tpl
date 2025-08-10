{{- define "demo-frontend.name" -}}
{{- .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "demo-frontend.fullname" -}}
{{- printf "%s-%s" .Release.Name (include "demo-frontend.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "demo-frontend.labels" -}}
app.kubernetes.io/name: {{ include "demo-frontend.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{- define "demo-frontend.selectorLabels" -}}
app.kubernetes.io/name: {{ include "demo-frontend.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
