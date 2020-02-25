%define _unpackaged_files_terminate_build 1

Name: yamp
Version: 0.1
Release: alt1
Summary: Unofficial player for Yandex.Music
License: MIT
Group: Sound
Url: https://github.com/amakeenk/yamp
Source: %name-%version.tar
Packager: Alexander Makeenkov <amakeenk@altlinux.org>

BuildArch: noarch
BuildRequires(pre): rpm-build-python3
BuildRequires: python3-module-setuptools
Requires: python3-module-%name

%description
%summary.

%package -n python3-module-%name
Summary: %summary
Group: Development/Python3
BuildArch: noarch

%description -n python3-module-%name
This package contains python module for %name.

%prep
%setup

%build
%python3_build

%install
%python3_install

%files
%_bindir/%name
%_desktopdir/%name.desktop

%files -n python3-module-%name
%python3_sitelibdir/%name
%python3_sitelibdir/%name-%version-py%_python3_version.egg-info

%changelog
* Tue Feb 25 2020 Alexander Makeenkov <amakeenk@altlinux.org> 0.1-alt1
- Initial build for ALT
