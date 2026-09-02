/* Ajustes específicos de interação do Corpus TEJ. */

(function () {
  function installDocumentPopupInteraction() {
    var tokinfo = document.getElementById('tokinfo');

    if (
      !tokinfo ||
      typeof window.showdocinfo !== 'function' ||
      typeof document.onmouseout !== 'function'
    ) {
      return;
    }

    var originalShowDocInfo = window.showdocinfo;
    var originalMouseOut = document.onmouseout;

    var documentPopupOpen = false;
    var trigger = null;
    var hideTimer = null;

    function cancelHide() {
      if (hideTimer !== null) {
        clearTimeout(hideTimer);
        hideTimer = null;
      }
    }

    function closeDocumentPopup() {
      cancelHide();
      documentPopupOpen = false;
      trigger = null;

      if (typeof window.hidetokinfo === 'function') {
        window.hidetokinfo();
      } else {
        tokinfo.style.display = 'none';
      }
    }

    function scheduleHide() {
      cancelHide();

      hideTimer = setTimeout(function () {
        if (
          tokinfo.matches(':hover') ||
          (trigger && trigger.matches(':hover'))
        ) {
          return;
        }

        closeDocumentPopup();
      }, 250);
    }

    window.showdocinfo = function (showelement) {
      cancelHide();
      documentPopupOpen = true;
      trigger = showelement;

      return originalShowDocInfo.apply(this, arguments);
    };

    document.onmouseout = function (evt) {
      if (!documentPopupOpen) {
        return originalMouseOut.call(document, evt);
      }

      var source = evt.target;
      var destination = evt.relatedTarget;

      if (
        source === tokinfo ||
        tokinfo.contains(source) ||
        destination === tokinfo ||
        (destination && tokinfo.contains(destination)) ||
        source === trigger ||
        (trigger && trigger.contains(source)) ||
        destination === trigger ||
        (destination && trigger.contains(destination))
      ) {
        scheduleHide();
        return;
      }

      return originalMouseOut.call(document, evt);
    };

    tokinfo.addEventListener('mouseenter', function () {
      if (documentPopupOpen) {
        cancelHide();
      }
    });

    tokinfo.addEventListener('mouseleave', function () {
      if (documentPopupOpen) {
        scheduleHide();
      }
    });
  }

  window.addEventListener('load', installDocumentPopupInteraction);
})();
