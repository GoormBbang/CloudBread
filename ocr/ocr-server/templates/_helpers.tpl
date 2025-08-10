{{- define "ocr-server.name" -}}
{{- .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "ocr-server.fullname" -}}
{{- printf "%s-%s" .Release.Name (include "ocr-server.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "ocr-server.labels" -}}
app.kubernetes.io/name: {{ include "ocr-server.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{- define "ocr-server.selectorLabels" -}}
app.kubernetes.io/name: {{ include "ocr-server.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
