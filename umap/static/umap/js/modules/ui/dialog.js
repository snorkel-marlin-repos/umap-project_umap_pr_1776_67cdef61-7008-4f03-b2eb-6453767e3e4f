import { DomUtil, DomEvent } from '../../../vendors/leaflet/leaflet-src.esm.js'
import { translate } from '../i18n.js'

export default class Dialog {
  constructor(parent) {
    this.parent = parent
    this.container = DomUtil.create('dialog', 'umap-dialog window', this.parent)
    DomEvent.disableClickPropagation(this.container)
    DomEvent.on(this.container, 'contextmenu', DomEvent.stopPropagation) // Do not activate our custom context menu.
    DomEvent.on(this.container, 'wheel', DomEvent.stopPropagation)
    DomEvent.on(this.container, 'MozMousePixelScroll', DomEvent.stopPropagation)
  }

  get visible() {
    return this.container.open
  }

  close() {
    this.container.close()
  }

  open({ className, content, modal } = {}) {
    this.container.innerHTML = ''
    if (modal) this.container.showModal()
    else this.container.show()
    if (className) {
      this.container.classList.add(className)
    }
    const buttonsContainer = DomUtil.create('ul', 'buttons', this.container)
    const closeButton = DomUtil.createButtonIcon(
      DomUtil.create('li', '', buttonsContainer),
      'icon-close',
      translate('Close')
    )
    DomEvent.on(closeButton, 'click', this.close, this)
    this.container.appendChild(buttonsContainer)
    this.container.appendChild(content)
  }
}
