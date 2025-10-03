{{- define "chatbot-server.name" -}}
{{- .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "chatbot-server.fullname" -}}
{{- printf "%s-%s" .Release.Name (include "chatbot-server.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "chatbot-server.labels" -}}
app.kubernetes.io/name: {{ include "chatbot-server.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{- define "chatbot-server.selectorLabels" -}}
app.kubernetes.io/name: {{ include "chatbot-server.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}