#
# Conditional build:
%bcond_with	spamassassin	# spamassassin
%bcond_without	clamav		# clamav

%define	groupid	210
%define	userid	210

%include	/usr/lib/rpm/macros.perl
Summary:	Content scanner for Qmail
Summary(pl):	Skaner zawarto¶ci dla Qmaila
Name:		qmail-scanner
Version:	1.24
Release:	3.23
License:	GPL
Group:		Applications/System
Source0:	http://dl.sourceforge.net/qmail-scanner/%{name}-%{version}.tgz
# Source0-md5:	0281b721b059e09c8470982d26e4ccb0
Source1:	%{name}.conf
Source2:	%{name}-report.sh
Patch0:		%{name}-root.patch
Patch1:		%{name}-extsub.patch
Patch2:		%{name}-localconf.patch
Patch3:		%{name}-localconf-vars.patch
Patch4:		%{name}-attach.patch
Patch5:		%{name}-perm.patch
Patch6:		%{name}-FHS.patch
URL:		http://qmail-scanner.sourceforge.net/
%{?with_clamav:BuildRequires:	clamav}
BuildRequires:	maildrop >= 1.3.8
BuildRequires:	perl-DB_File >= 1.803
BuildRequires:	perl-base >= 1:5.6.1
BuildRequires:	rpmbuild(macros) >= 1.159
%if %{with spamassassin}
BuildRequires:	spamassassin
BuildRequires:	spamassassin-spamc
%endif
Requires(pre):	/usr/bin/getgid
Requires(pre):	/bin/id
Requires(pre):	/usr/sbin/groupadd
Requires(pre):	/usr/sbin/useradd
Requires(post):	sed >= 4.0
Requires(postun):	/usr/sbin/userdel
Requires(postun):	/usr/sbin/groupdel
%{?with_clamav:Requires:	clamav}
Requires:	fileutils
Requires:	maildrop >= 1.3.8
Requires:	qmail >= 1.03-56.50
%if %{with spamassassin}
Requires:	spamassassin
Requires:	spamassassin-spamc
%endif
Provides:	user(qscand)
Provides:	group(qscand)
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

%description -l pl
Qmail-Scanner to dodatek umo¿liwiaj±cy serwerowi poczty elektronicznej
Qmail skanowanie ca³ej przekazywanej poczty pod k±tem danych cech
(tzn. skanowanie zawarto¶ci). Zwykle jest u¿ywany dla funkcji
zabezpieczeñ antywirusowych, w którym to przypadku jest u¿ywany w
po³±czeniu z zewnêtrznymi skanerami antywirusowymi, ale umo¿liwia
tak¿e reagowanie (na poziomie serwera) na pocztê zawieraj±c± konkretne
³añcuchy w pewnych nag³ówkach, albo pewne nazwy plików lub typy
za³±czników (np. za³±czniki *.VBS). Mo¿e byæ u¿ywany tak¿e jako
narzêdzie archiwizuj±ce do audytu lub kopii zapasowych. Qmail-Scanner
jest zintegrowany z serwerem pocztowym na poziomie ni¿szym ni¿ inne
uniksowe skanery antywirusowe, czego efektem jest lepsza wydajno¶æ.
Program mo¿e skanowaæ nie tylko lokalnie wysy³an±/dostarczan± pocztê,
ale tak¿e pocztê przekazywan± przez serwer (relaying).

%prep
%setup -q
# Take out root install requirement.
%patch0 -p1
# load sub-$SCANNER.pl if needed.
%patch1 -p1
# require /etc/qmail-scanner.conf
%patch2 -p1
# make overriden vars as $our
%patch3 -p1
# disallow by default common ms-windows executables
%patch4 -p1
# allow group read permissions in tmp files
%patch5 -p1
%patch6 -p0 -b .FHS

%build
scanners=`echo \
%{?with_clamav:clamscan clamdscan} \
%{?with_spamassassin:verbose_spamassassin fast_spamassassin} \
`
scanners=$(echo "$scanners" | tr ' ' ',')

LANG=en_GB \
./configure \
	--qs-user %(id -un) \
	--domain localhost \
	--batch \
	--debug no \
	--log-details no \
	--skip-setuid-test \
	--no-QQ-check \
	--admin root \
	--notify none \
	--block-password-protected \
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

# Install quarantine
install quarantine-attachments.txt $RPM_BUILD_ROOT/var/spool/qmailscan

# touch file, so we could add it to paackage
> $RPM_BUILD_ROOT/var/spool/qmailscan/qmail-scanner-queue-version.txt

> $RPM_BUILD_ROOT/var/spool/qmailscan/quarantine.log
> $RPM_BUILD_ROOT/var/spool/qmailscan/qmail-queue.log
> $RPM_BUILD_ROOT/var/spool/qmailscan/quarantine-attachments.db

# Install virus scanner subroutines
for s in sub-*.pl; do
	install $s $RPM_BUILD_ROOT%{_libdir}/%{name}
	echo "1;" >> $RPM_BUILD_ROOT%{_libdir}/%{name}/$s

	ln -s %{_libdir}/%{name}/$s $RPM_BUILD_ROOT/var/spool/qmailscan/$s
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
			/etc/rc.d/init.d/clamd restart >&2
		fi
	fi
fi
%endif

%post
# setup vars once
if grep -q MAILDOMAIN /etc/qmail-scanner.conf; then
	cp /etc/qmail-scanner.conf /etc/qmail-scanner.conf.tmp
	hostname=$(hostname -f 2>/dev/null || echo localhost)
	sed -e "
		s/MAILDOMAIN/$hostname/g
		s/USERNAME/root/g
	" /etc/qmail-scanner.conf.tmp > /etc/qmail-scanner.conf
	rm -f /etc/qmail-scanner.conf.tmp
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
make -s -C /etc/tcprules.d

%pre
[ "`/usr/bin/getgid qscand`" ] || \
	/usr/sbin/groupadd -g %{groupid} qscand

[ "`/bin/id -u qscand 2>/dev/null`" ] || \
	/usr/sbin/useradd -u %{userid} -d /var/spool/qmailscan \
		-s /bin/false -g qscand -c "Qmail-Scanner Account" qscand

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
%doc contrib/spamc-nice.eml contrib/test-trophie.pl contrib/logrotate.qmailscanner contrib/sub-avpdaemon.pl
%doc contrib/logging_first_80_chars.eml contrib/spamc-nasty.eml contrib/avpdeamon.init contrib/test_installation.sh
%doc contrib/test-sophie.pl contrib/reformime-test.eml contrib/sub-sender-cache.pl contrib/rbl_scanner.txt
%doc contrib/test-clamd.pl contrib/qs2mrtg.pl contrib/mrtg-qmail-scanner.cfg

%config(noreplace) %{_sysconfdir}/qmail-scanner.conf

%dir %{_libdir}/%{name}
%attr(755,root,root) %config %{_libdir}/%{name}/qmail-scanner-queue.pl
%attr(6755,qscand,qscand) %{_libdir}/%{name}/qmail-scanner-queue

%dir %attr(750,qscand,qscand) /var/spool/qmailscan
%dir %attr(2750,qscand,qscand) /var/spool/qmailscan/tmp

%attr(700,qscand,qscand) /var/spool/qmailscan/archives
%attr(700,qscand,qscand) /var/spool/qmailscan/failed
%attr(700,qscand,qscand) /var/spool/qmailscan/quarantine
%attr(700,qscand,qscand) /var/spool/qmailscan/working

%attr(644,qscand,qscand) %config(noreplace) %verify(not size mtime md5) /var/spool/qmailscan/*.log
%attr(640,qscand,qscand) %verify(not size mtime md5) /var/spool/qmailscan/*.db

# scanner subs
%{_libdir}/%{name}/*.pl

/var/spool/qmailscan/qmail-scanner-queue-version.txt
%config(noreplace) /var/spool/qmailscan/quarantine-attachments.txt

# reports of viruses per day
%dir /var/spool/qmailscan/reports
%attr(755,root,root) %{_libdir}/%{name}/report.sh
