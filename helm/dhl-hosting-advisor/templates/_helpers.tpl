{{/* Release name is used directly as the resource-name prefix. */}}
{{- define "dha.name" -}}
{{ .Release.Name }}
{{- end }}

{{- define "dha.labels" -}}
app.kubernetes.io/part-of: dhl-hosting-advisor
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "dha.componentLabels" -}}
{{ include "dha.labels" . }}
app.kubernetes.io/component: {{ .component }}
{{- end }}

{{- define "dha.scheme" -}}
{{- if .Values.route.tls }}https{{- else }}http{{- end }}
{{- end }}

{{- define "dha.frontendHost" -}}
{{ .Release.Name }}.{{ .Values.route.domain }}
{{- end }}

{{- define "dha.backendHost" -}}
{{ .Release.Name }}-backend.{{ .Values.route.domain }}
{{- end }}

{{- define "dha.idpHost" -}}
{{ .Release.Name }}-idp.{{ .Values.route.domain }}
{{- end }}

{{- define "dha.frontendUrl" -}}
{{ include "dha.scheme" . }}://{{ include "dha.frontendHost" . }}
{{- end }}

{{- define "dha.backendUrl" -}}
{{ include "dha.scheme" . }}://{{ include "dha.backendHost" . }}
{{- end }}

{{- define "dha.idpUrl" -}}
{{ include "dha.scheme" . }}://{{ include "dha.idpHost" . }}
{{- end }}

{{- define "dha.image" -}}
{{ .Values.image.registry }}/{{ .Values.namespace }}/{{ .name }}:{{ .Values.image.tag }}
{{- end }}
