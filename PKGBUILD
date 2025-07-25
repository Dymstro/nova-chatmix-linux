pkgname=nova-chatmix
pkgver=0.0.1
pkgrel=1
arch=('x86_64')
depends=('python' 'python-hid' 'pipewire')
makedepends=('git')
source=("$pkgname::git+https://github.com/Dymstro/nova-chatmix-linux.git")
sha256sums=('SKIP')
install=nova-chatmix.install

package() {
  cd "$pkgname"
  install -Dm755 nova.py "$pkgdir/usr/bin/nova-chatmix"
  install -Dm644 50-nova-pro-wireless.rules \
       "$pkgdir/usr/lib/udev/rules.d/50-nova-pro-wireless.rules"
  install -Dm644 nova-chatmix.service \
       "$pkgdir/usr/lib/systemd/user/nova-chatmix.service"
  install -Dm644 README.md "$pkgdir/usr/share/doc/$pkgname/README.md"
}
