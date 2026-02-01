const output = document.getElementById('results');
const runButton = document.getElementById('run-tests');
const frame = document.getElementById('app-frame');

function log(message) {
  output.textContent += `\n${message}`;
}

function resetOutput() {
  output.textContent = '';
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function wait(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function waitFor(fn, timeout = 5000, interval = 100) {
  const start = Date.now();
  while (Date.now() - start < timeout) {
    if (fn()) return true;
    await wait(interval);
  }
  return false;
}

async function runTests() {
  resetOutput();
  log('⏳ Démarrage des tests...');

  const win = frame.contentWindow;
  const doc = frame.contentDocument;

  if (!win || !doc) {
    throw new Error('Iframe non chargé');
  }

  const ready = await waitFor(() => typeof win.searchCities === 'function', 8000);
  assert(ready, 'App non prête (searchCities indisponible)');
  log('✓ App chargée');

  await win.ensureIndexLoaded();
  assert(Array.isArray(win.communesIndex) && win.communesIndex.length > 1000, 'Index non chargé');
  log('✓ Index chargé');

  const input = doc.getElementById('city-search');
  input.value = 'Paris';
  await win.onCitySearchInput('Paris');
  await wait(400);

  const dropdown = doc.getElementById('autocomplete-dropdown');
  assert(!dropdown.classList.contains('hidden'), 'Autocomplete non affichée');
  const firstItem = dropdown.querySelector('li');
  assert(firstItem, 'Aucune suggestion');
  firstItem.click();
  await wait(200);

  assert(win.searchZones.length > 0, 'Zone non ajoutée');
  log('✓ Autocomplete + ajout zone');

  doc.getElementById('min-pop').value = '5000';
  doc.getElementById('max-pop').value = '50000';

  await win.searchCities();

  const hasResults = await waitFor(() => win.searchResults && win.searchResults.length > 0, 10000);
  assert(hasResults, 'Aucun résultat après recherche');
  log(`✓ Recherche ok (${win.searchResults.length} résultats)`);

  win.saveResults();
  await wait(200);
  const shareInput = doc.getElementById('share-link-inline');
  assert(shareInput && shareInput.value.includes('results.html?q='), 'Lien de partage invalide');
  log('✓ Lien de partage généré');

  log('\n✅ Tous les tests sont passés.');
}

runButton.addEventListener('click', async () => {
  runButton.disabled = true;
  try {
    await runTests();
  } catch (error) {
    log(`\n❌ Échec: ${error.message}`);
  } finally {
    runButton.disabled = false;
  }
});
