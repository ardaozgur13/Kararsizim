/**
 * kararsızım — Sayfa Yenilenmeden Oy Verme ve Canlı Sonuçlar (poll.js)
 */

document.addEventListener('DOMContentLoaded', function () {
  const voteForm = document.getElementById('vote-form');
  const voteSection = document.getElementById('vote-section');
  const resultsSection = document.getElementById('results-section');
  const voteErrorAlert = document.getElementById('vote-error-alert');
  const voteSubmitBtn = document.getElementById('vote-submit-btn');

  // Sayfa ilk yüklendiğinde var olan sonuç çubuklarının dolma animasyonunu tetikle
  animateExistingBars();

  function animateExistingBars() {
    const bars = document.querySelectorAll('.result-bar-bg');
    requestAnimationFrame(() => {
      bars.forEach(bar => {
        const targetWidth = bar.getAttribute('data-percentage') || '0';
        bar.style.width = targetWidth + '%';
      });
    });
  }

  if (!voteForm) return;

  voteForm.addEventListener('submit', function (e) {
    e.preventDefault();

    const selectedOption = voteForm.querySelector('input[name="option_id"]:checked');
    if (!selectedOption) {
      showError('Lütfen oy vermek için bir seçenek işaretleyin.');
      return;
    }

    // Butonu pasif yap
    if (voteSubmitBtn) {
      voteSubmitBtn.disabled = true;
      voteSubmitBtn.textContent = 'Oyun Kaydediliyor...';
    }
    hideError();

    const formData = new FormData(voteForm);

    fetch(voteForm.action, {
      method: 'POST',
      body: formData,
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
      },
    })
      .then(response => {
        return response.json().then(data => ({
          status: response.status,
          ok: response.ok,
          data: data,
        }));
      })
      .then(({ ok, data }) => {
        if (!ok || !data.success) {
          const msg = (data && data.error) ? data.error : 'Oy verilirken bir hata oluştu.';
          showError(msg);
          if (voteSubmitBtn) {
            voteSubmitBtn.disabled = false;
            voteSubmitBtn.textContent = 'Oyumu Kullan';
          }
          return;
        }

        // Başarılı oy verme: Sonuçları render et
        renderResults(data);
      })
      .catch(error => {
        console.error('Oy verme hatası:', error);
        // Ağ hatası veya fetch sorunu durumunda klasik form gönderimine fallback yap
        voteForm.submit();
      });
  });

  function showError(msg) {
    if (voteErrorAlert) {
      voteErrorAlert.textContent = msg;
      voteErrorAlert.style.display = 'block';
    }
  }

  function hideError() {
    if (voteErrorAlert) {
      voteErrorAlert.style.display = 'none';
      voteErrorAlert.textContent = '';
    }
  }

  function renderResults(data) {
    if (!resultsSection) return;

    // Oy verme formunu gizle
    if (voteSection) {
      voteSection.style.display = 'none';
    }

    const resultsList = resultsSection.querySelector('.results-list');
    const totalVotesSpan = resultsSection.querySelector('.total-votes-count');

    if (totalVotesSpan) {
      totalVotesSpan.textContent = data.total_votes;
    }

    if (resultsList) {
      resultsList.innerHTML = '';

      data.options.forEach(opt => {
        const item = document.createElement('div');
        item.className = 'result-item' + (opt.is_selected ? ' user-voted' : '');

        item.innerHTML = `
          <div class="result-bar-bg" data-percentage="${opt.percentage}" style="width: 0%;"></div>
          <div class="result-content">
            <div class="result-label">
              <span>${escapeHtml(opt.text)}</span>
              ${opt.is_selected ? '<span class="vote-badge">✓ Senin Oyun</span>' : ''}
            </div>
            <div class="result-stats">
              <span class="result-percentage">%${opt.percentage}</span>
              <span class="result-count">(${opt.votes_count} oy)</span>
            </div>
          </div>
        `;

        resultsList.appendChild(item);
      });
    }

    // Sonuç bölümünü görünür yap
    resultsSection.style.display = 'block';

    // Animasyonla çubukları doldur
    setTimeout(animateExistingBars, 50);
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
});
