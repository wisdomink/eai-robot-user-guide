export interface PresetSelection {
  id: string
  scope: string
  text: string
}

/** Only attach a selection to its user-message request, never history/actions. */
export function matchesPresetMessage(body: string, selection: PresetSelection): boolean {
  try {
    const request = JSON.parse(body)
    if (!['threads.create', 'threads.add_user_message'].includes(request.type)) return false
    const content = request.params?.input?.content
    return Array.isArray(content) && content.length === 1
      && content[0].type === 'input_text' && content[0].text === selection.text
  } catch {
    return false
  }
}
