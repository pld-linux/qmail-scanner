#
# Conditional build:
%bcond_with	spamassassin	# spamassassin
%bcond_without	clamav		# clamav

%include	/usr/lib/rpm/macros.perl
Summary:	Content scanner for Qmail
Summary(pl.UTF-8):	Skaner zawartości dla Qmaila
Name:		qmail-scanner
Version:	2.04
Release:	0.1
License:	GPL
Group:		Applications/Mail
Source0:	http://dl.sourceforge.net/qmail-scanner/%{name}-%{version}.tgz
# Source0-md5:	b11d2f177074ad6b4b68b93de227d78e
Source1:	%{name}.conf
Source2:	%{name}-report.sh
Patch0:		%{name}-root.patch
Patch1:		%{name}-extsub.patch
Patch2:		%{name}-localconf.patch
Patch3:		%{name}-localconf-vars.patch
Patch4:		%{name}-attach.patch
Patch6:		%{name}-FHS.patch
Patch7:		%{name}-qinject.patch
URL:		http://qmail-scanner.sourceforge.net/
%{?with_clamav:BuildRequires:	clamav}
BuildRequires:	daemontools
BuildRequires:	maildrop >= 1.3.8
BuildRequires:	perl-DB_File >= 1.803
BuildRequires:	perl-base >= 1:5.6.1
BuildRequires:	rpmbuild(macros) >= 1.202
%if %{with spamassassin}
BuildRequires:	spamassassin
BuildRequires:	spamassassin-spamc
%endif
Requires(post):	sed >= 4.0
Requires(postun):	/usr/sbin/groupdel
Requires(postun):	/usr/sbin/userdel
Requires(pre):	/bin/id
Requires(pre):	/usr/bin/getgid
Requires(pre):	/usr/sbin/groupadd
Requires(pre):	/usr/sbin/useradd
%{?with_clamav:Requires:	clamav}
Requires:	fileutils
Requires:	maildrop >= 1.3.8
Requires:	qmail >= 1.03-56.50
%if %{with spamassassin}
Requires:	spamassassin
Requires:	spamassassin-spamc
%endif
Provides:	group(qscand)
Provides:	user(qscand)
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%description
Qmail-Scanner is an addon that enables a Qmail email server to scan
all gateway-ed email for certain characteristics (i.e. a content
scanner). It is typically used for its anti-virus protection
functions, in which case it is used in conjunction with external virus
scanners, but also enables a site (at a server/site level) to react to
email that contains specific strings in particular headers, or
particular attachment filenames or types (e.g. *.VBS attachments). It
also can be used as an archiving tool for auditing or backup purposes.
Qmail-Scanner is integrated into the mail server at a lower level than
some other Unix-based virus scanners, resulting in better performance.
It is capable of scanning not only locally sent/received email, but
also email that crosses the server in a relay capacity.

%description -l pl.UTF-8
Qmail-Scanner to dodatek umożliwiający serwerowi poczty elektronicznej
Qmail skanowanie całej przekazywanej poczty pod kątem danych cech
(tzn. skanowanie zawartości). Zwykle jest używany dla funkcji
zabezpieczeń antywirusowych, w którym to przypadku jest używany w
połączeniu z zewnętrznymi skanerami antywirusowymi, ale umożliwia
także reagowanie (na poziomie serwera) na pocztę zawierającą konkretne
łańcuchy w pewnych nagłówkach, albo pewne nazwy plików lub typy
załączników (np. załączniki *.VBS). Może być używany także jako
narzędzie archiwizujące do audytu lub kopii zapasowych. Qmail-Scanner
jest zintegrowany z serwerem pocztowym na poziomie niższym niż inne
uniksowe skanery antywirusowe, czego efektem jest lepsza wydajność.
Program może skanować nie tylko lokalnie wysyłaną/dostarczaną pocztę,
ale także pocztę przekazywaną przez serwer (relaying).

%prep
%setup -q
# Take out root install requirement.
%patch0 -p1
# load sub-$SCANNER.pl if needed.
%patch1 -p1
# require %{_sysconfdir}/qmail-scanner.conf
%patch2 -p1
# make overriden vars as $our
%patch3 -p1
# disallow by default common ms-windows executables
%patch4 -p1
%patch6 -p0
%patch7 -p1

%build
scanners=$(echo \
%{?with_clamav:clamscan clamdscan} \
%{?with_spamassassin:verbose_spamassassin fast_spamassassin} \
)
scanners=$(echo "$scanners" | tr ' ' ',')

./configure \
	--spooldir /var/spool/qmailscan \
	--qmaildir /var/qmail \
	--bindir /var/qmail/bin \
	--qmail-queue-binary /var/qmail/bin/qmail-queue \
	--qmail-inject-binary /var/qmail/bin/qmail-inject \
	--qs-user %(id -un) \
	--domain localhost \
	--batch \
	%{!?debug:--debug no} \
	--log-details no \
	--skip-setuid-test \
	--no-QQ-check \
	--admin root \
	--notify none \
	--lang en_GB \
	--scanners ${scanners:-none}

# build for qmail-scanner-queue wrapper, so we don't need suidperl
cd contrib
%{__cc} %{rpmcflags} -o qmail-scanner-queue qmail-scanner-queue.c

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT%{_sysconfdir}
install -d $RPM_BUILD_ROOT%{_libdir}/%{name}
install -d $RPM_BUILD_ROOT/var/spool/qmailscan/tmp

# Create maildirs.
install -d $RPM_BUILD_ROOT/var/spool/qmailscan/{archives,failed,quarantine,working}/{cur,new,tmp}

# Install configuration file.
install %{SOURCE1} $RPM_BUILD_ROOT%{_sysconfdir}

install -d $RPM_BUILD_ROOT/var/spool/qmailscan/reports
install %{SOURCE2} $RPM_BUILD_ROOT%{_libdir}/%{name}/report.sh

# Install executable.
install qmail-scanner-queue.pl $RPM_BUILD_ROOT%{_libdir}/%{name}
install contrib/qmail-scanner-queue $RPM_BUILD_ROOT%{_libdir}/%{name}

# Install quarantine.
install quarantine-events.txt $RPM_BUILD_ROOT/var/spool/qmailscan

# touch file, so we could add it to package
> $RPM_BUILD_ROOT/var/spool/qmailscan/qmail-scanner-queue-version.txt

> $RPM_BUILD_ROOT/var/spool/qmailscan/quarantine.log
> $RPM_BUILD_ROOT/var/spool/qmailscan/qmail-queue.log
> $RPM_BUILD_ROOT/var/spool/qmailscan/quarantine-events.db

# Install virus scanner subroutines
for s in sub-*.pl; do
	install $s $RPM_BUILD_ROOT%{_libdir}/%{name}
	echo "1;" >> $RPM_BUILD_ROOT%{_libdir}/%{name}/$s
done

%clean
rm -rf $RPM_BUILD_ROOT

%if %{with clamav}
%triggerin -- clamav
# Initialize the version file, as clamav version might have changed
%{_libdir}/%{name}/qmail-scanner-queue -z

groups=$(id -Gn clamav)
if [[ "$groups" != *qscand* ]]; then
	# add qscand group to clamav
	QSCAND=$(/usr/bin/getgid qscand)
	if [ $? -eq 0 ]; then
		# NOTE:
		# Not to wipe out other groups clamav could have,
		# we specify full list of groups.
		%{_sbindir}/usermod -G $(echo $groups qscand | tr ' ' ',') clamav
		echo "Adding clamav to qscand group GID=$QSCAND"
		if [ -f /var/lock/subsys/clamd ]; then
			/sbin/service clamd restart
		fi
	fi
fi
%endif

%post
# setup vars once
if grep -q MAILDOMAIN %{_sysconfdir}/qmail-scanner.conf; then
	cp -f %{_sysconfdir}/qmail-scanner.conf{,.rpmsave}
	hostname=$(hostname -f 2>/dev/null || echo localhost)
	sed -i -e "
		s/MAILDOMAIN/$hostname/g
		s/USERNAME/root/g
	" %{_sysconfdir}/qmail-scanner.conf
fi

# Initialize the version file.
%{_libdir}/%{name}/qmail-scanner-queue -z

# Initialize the perlscanner database.
%{_libdir}/%{name}/qmail-scanner-queue -g

%triggerpostun -- %{name} < 1.24-3.22
# upgrade qmail-scanner path in tcprules
for s in qmtp smtp; do
	if [ -f /etc/tcprules.d/tcp.qmail-$s ]; then
		sed -i -e '
		s,/var/qmail/bin/qmail-scanner-queue\(\.pl\)\?,%{_libdir}/%{name}/qmail-scanner-queue,
		' /etc/tcprules.d/tcp.qmail-$s
	fi
done
%{__make} -s -C /etc/tcprules.d

%pre
%groupadd -g 210 qscand
%useradd -u 210 -d /var/spool/qmailscan -g qscand -c "Qmail-Scanner Account" qscand

%postun
if [ "$1" = "0" ]; then
	%userremove qscand
	%groupremove qscand
fi

%files
%defattr(644,root,root,755)
%doc README CHANGES COPYING
# html
%doc README.html FAQ.php TODO.php configure-options.php manual-install.php perlscanner.php
# and contrib
%doc contrib/spamc-nice.eml contrib/test-trophie.pl contrib/logrotate.qmail-scanner contrib/sub-avpdaemon.pl
%doc contrib/logging_first_80_chars.eml contrib/spamc-nasty.eml contrib/avpdeamon.init contrib/test_installation.sh
%doc contrib/test-sophie.pl contrib/reformime-test.eml contrib/sub-sender-cache.pl contrib/rbl_scanner.txt
%doc contrib/test-clamd.pl contrib/qs2mrtg.pl contrib/mrtg-qmail-scanner.cfg

%config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/qmail-scanner.conf

%dir %{_libdir}/%{name}
%config %attr(755,root,root) %{_libdir}/%{name}/qmail-scanner-queue.pl
%attr(6755,qscand,qscand) %{_libdir}/%{name}/qmail-scanner-queue

%dir %attr(750,qscand,qscand) /var/spool/qmailscan
%dir %attr(2750,qscand,qscand) /var/spool/qmailscan/tmp

%attr(700,qscand,qscand) /var/spool/qmailscan/archives
%attr(700,qscand,qscand) /var/spool/qmailscan/failed
%attr(700,qscand,qscand) /var/spool/qmailscan/quarantine
%attr(700,qscand,qscand) /var/spool/qmailscan/working

%attr(644,qscand,qscand) %config(noreplace) %verify(not md5 mtime size) /var/spool/qmailscan/*.log
%attr(640,qscand,qscand) %verify(not md5 mtime size) /var/spool/qmailscan/*.db

# scanner subs
%{_libdir}/%{name}/sub-*.pl

%config(noreplace) %verify(not md5 mtime size) /var/spool/qmailscan/qmail-scanner-queue-version.txt
%config(noreplace) %verify(not md5 mtime size) /var/spool/qmailscan/quarantine-events.txt

# reports of viruses per day
%dir /var/spool/qmailscan/reports
%attr(755,root,root) %{_libdir}/%{name}/report.sh
