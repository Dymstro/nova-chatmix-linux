Name:           nova-chatmix
Version:        0.1.0
Release:        1%{?dist}
Summary:        ChatMix Implementation for the SteelSeries Arctis Nova Pro Wireless headset

License:        0BSD
URL:            https://git.dymstro.nl/Dymstro/nova-chatmix-linux
Source0:        %{name}-%{version}.tar.gz

BuildRequires:  systemd-rpm-macros
Requires:       python3,python3-hidapi,pipewire,pulseaudio-utils

BuildArch:      noarch

%description
ChatMix Implementation for the SteelSeries Arctis Nova Pro Wireless headset

%prep
%setup -qc
# Change service to point to system bin directory
sed -i 's#%h/\.local/bin#%{_bindir}#g' nova-chatmix.service

%install
install -Dm 0755 nova-chatmix.py %{buildroot}/%{_bindir}/nova-chatmix
install -Dm 0644 50-nova-pro-wireless.rules %{buildroot}/%{_libdir}/udev/rules.d/50-nova-pro-wireless.rules
install -Dm 0644 nova-chatmix.service %{buildroot}/%{_libdir}/systemd/user/nova-chatmix.service

%post
udevadm control --reload-rules
udevadm trigger
%systemd_user_post nova-chatmix.service

%preun
%systemd_user_preun nova-chatmix.service

%postun
%systemd_user_postun_with_restart nova-chatmix.service
%systemd_user_postun nova-chatmix.service


%files
%license LICENSE
%doc README.md
%{_bindir}/nova-chatmix
%{_libdir}/udev/rules.d/50-nova-pro-wireless.rules
%{_libdir}/systemd/user/nova-chatmix.service


%changelog
* Sat Aug 16 2025 Ricardo <ricardo@dymstro.nl>
- Release 0.1.0
