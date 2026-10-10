/**
 * kararsızım — Dinamik Seçenek Ekleme / Çıkarma (create_poll.js)
 * Kural: En az 2, en fazla 5 seçenek.
 */

document.addEventListener('DOMContentLoaded', function () {
  const optionsContainer = document.getElementById('options-container');
  const addOptionBtn = document.getElementById('add-option-btn');
  const minOptions = 2;
  const maxOptions = 5;

  if (!optionsContainer || !addOptionBtn) return;

  function updateButtonsState() {
    const optionRows = optionsContainer.querySelectorAll('.option-row');
    const count = optionRows.length;

    // Seçenek ekleme butonunu sınırla
    if (count >= maxOptions) {
      addOptionBtn.disabled = true;
      addOptionBtn.textContent = 'En fazla 5 seçenek ekleyebilirsin';
    } else {
      addOptionBtn.disabled = false;
      addOptionBtn.textContent = '+ Seçenek Ekle';
    }

    // Her satırdaki silme butonunu güncelle
    optionRows.forEach((row, index) => {
      const removeBtn = row.querySelector('.remove-option-btn');
      const input = row.querySelector('input');
      if (input) {
        input.placeholder = `Seçenek ${index + 1}`;
      }
      if (removeBtn) {
        if (count <= minOptions) {
          removeBtn.disabled = true;
          removeBtn.style.opacity = '0.3';
          removeBtn.title = 'En az 2 seçenek gereklidir';
        } else {
          removeBtn.disabled = false;
          removeBtn.style.opacity = '1';
          removeBtn.title = 'Bu seçeneği kaldır';
        }
      }
    });
  }

  // Seçenek ekleme
  addOptionBtn.addEventListener('click', function () {
    const currentCount = optionsContainer.querySelectorAll('.option-row').length;
    if (currentCount >= maxOptions) return;

    const nextIndex = currentCount + 1;
    const newRow = document.createElement('div');
    newRow.className = 'option-row';
    newRow.style.display = 'flex';
    newRow.style.alignItems = 'center';
    newRow.style.gap = '0.5rem';
    newRow.style.marginBottom = '0.6rem';

    newRow.innerHTML = `
      <input type="text" name="options" class="form-control" placeholder="Seçenek ${nextIndex}" maxlength="100" required>
      <button type="button" class="btn btn-outline btn-sm remove-option-btn" aria-label="Seçeneği sil">✕</button>
    `;

    optionsContainer.appendChild(newRow);
    const newInput = newRow.querySelector('input');
    if (newInput) newInput.focus();

    updateButtonsState();
  });

  // Seçenek kaldırma (event delegation)
  optionsContainer.addEventListener('click', function (e) {
    if (e.target && e.target.closest('.remove-option-btn')) {
      const currentCount = optionsContainer.querySelectorAll('.option-row').length;
      if (currentCount > minOptions) {
        const row = e.target.closest('.option-row');
        if (row) {
          row.remove();
          updateButtonsState();
        }
      }
    }
  });

  // İlk yüklemede durumları ayarla
  updateButtonsState();
});
