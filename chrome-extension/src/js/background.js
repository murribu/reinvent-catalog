console.log(chrome.windows);

chrome.windows.onCreated.addListener(function() {
  console.log('window created');
});
