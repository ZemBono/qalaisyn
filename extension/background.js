// Clicking the toolbar icon does the same as Alt+Q in the focused field.
chrome.action.onClicked.addListener(tab => {
  if (tab.id) chrome.tabs.sendMessage(tab.id, { qalaisyn: "run" }).catch(() => {});
});
