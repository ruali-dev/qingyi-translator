var PaperTranslatorConnector;

function startup({ rootURI }, reason) {
  Services.scriptloader.loadSubScript(rootURI + "content/connector.js");
  PaperTranslatorConnector.startup();
}

function shutdown({ rootURI }, reason) {
  if (reason === APP_SHUTDOWN) return;
  PaperTranslatorConnector?.shutdown();
  PaperTranslatorConnector = undefined;
}

function install() {}
function uninstall() {}

