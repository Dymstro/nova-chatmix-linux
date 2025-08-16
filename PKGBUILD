# Maintainer: Dymstro <ricardo at dymstro dot nl>

pkgname=nova-chatmix
pkgver=0.1.0
pkgrel=1
arch=('any')
url='https://git.dymstro.nl/Dymstro/nova-chatmix-linux'
license=('0BSD')
depends=('python' 'python-hidapi' 'pipewire' 'libpulse')
makedepends=('git')
source=("$pkgname::git+https://git.dymstro.nl/Dymstro/nova-chatmix-linux.git#tag=v${pkgver}")
sha256sums=('SKIP')
install=nova-chatmix.install

prepare() {
  # Change service to point to system bin directory
  sed -i 's#%h/\.local/bin#/usr/bin#g' ${pkgname}/nova-chatmix.service
}

package() {
  cd "${pkgname}"
  install -Dm755 nova-chatmix.py "${pkgdir}/usr/bin/nova-chatmix/nova-chatmix"
  install -Dm644 50-nova-pro-wireless.rules "${pkgdir}/usr/lib/udev/rules.d/50-nova-pro-wireless.rules"
  install -Dm644 nova-chatmix.service "${pkgdir}/usr/lib/systemd/user/nova-chatmix.service"
  install -Dm644 README.md "${pkgdir}/usr/share/doc/${pkgname}/README.md"
  install -Dm644 LICENSE "${pkgdir}/usr/share/licenses/${pkgname}/LICENSE"
}
