#
# TODO: eliminate groupadd/useradd from %build, it will fail
#
# Conditional build:
%bcond_with	spamassassin	# spamassassin
%bcond_without	clamav		# clamav

%define	groupid	210
%define	userid	210

Summary:	Content scanner for Qmail
Summary(pl):	Skaner zawarto¶ci dla Qmaila
Name:		qmail-scanner
Version:	1.24
Release:	1
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
URL:		http://qmail-scanner.sourceforge.net/
%{?with_clamav:BuildRequires:	clamav}
BuildRequires:	maildrop >= 1.3.8
BuildRequires:	perl >= 5.6.1
BuildRequires:	perl(DB_File) >= 1.803
BuildRequires:	qmail-maildirmake
BuildRequires:	rpmbuild(macros) >= 1.159
%if %{with spamassassin}
BuildRequires:	spamassassin
BuildRequires:	spamassassin-spamc
%endif
Requires(pre):	/usr/bin/getgid
Requires(pre):	/bin/id
Requires(pre):	/usr/sbin/groupadd
Requires(pre):	/usr/sbin/useradd
Requires(postun):	/usr/sbin/userdel
Requires(postun):	/usr/sbin/groupdel
%{?with_clamav:Requires:	clamav}
Requires:	fileutils
Requires:	maildrop >= 1.3.8
Requires:	perl >= 1:5.6.1
Requires:	perl-DB_File >= 1.803
Requires:	perl-Time-HiRes >= 1.20
Requires:	qmail
%if %{with spamassassin}
Requires:	spamassassin
Requires:	spamassassin-spamc
%endif
Provides:	user(qscand)
Provides:	group(qscand)
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

# not FHS compliant
%define		varqmail	/var/qmail

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

%build
# create users. configure fails. DAMMIT
[ "`getgid qscand`" ] || \
/usr/sbin/groupadd -g %{groupid} -r -f qscand

[ "`id -u qscand 2>/dev/null`" ] || \
/usr/sbin/useradd -u %{userid} -o -M -r -d /var/spool/qmailscan -s /bin/false -g qscand -c "Qmail-Scanner Account" qscand

scanners=`echo \
%{?with_clamav:clamscan clamdscan} \
%{?with_spamassassin:verbose_spamassassin fast_spamassassin} \
`
scanners=$(echo "$scanners" | tr ' ' ',')

LANG=en_GB \
./configure \
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
install -d $RPM_BUILD_ROOT%{varqmail}/bin
install -d $RPM_BUILD_ROOT/var/spool/qmailscan/tmp

maildirmake $RPM_BUILD_ROOT/var/spool/qmailscan/archives
maildirmake $RPM_BUILD_ROOT/var/spool/qmailscan/failed
maildirmake $RPM_BUILD_ROOT/var/spool/qmailscan/quarantine
maildirmake $RPM_BUILD_ROOT/var/spool/qmailscan/working

# Install configuration file.
install %{SOURCE1} $RPM_BUILD_ROOT%{_sysconfdir}

install -d $RPM_BUILD_ROOT/var/spool/qmailscan/reports
install %{SOURCE2} $RPM_BUILD_ROOT/var/spool/qmailscan/report.sh

# Install executable.
install qmail-scanner-queue.pl $RPM_BUILD_ROOT%{varqmail}/bin
install contrib/qmail-scanner-queue $RPM_BUILD_ROOT%{varqmail}/bin

# Install quarantine
install quarantine-attachments.txt $RPM_BUILD_ROOT/var/spool/qmailscan

# touch file, so we could add it to paackage
> $RPM_BUILD_ROOT/var/spool/qmailscan/qmail-scanner-queue-version.txt

> $RPM_BUILD_ROOT/var/spool/qmailscan/quarantine.log
> $RPM_BUILD_ROOT/var/spool/qmailscan/qmail-queue.log
> $RPM_BUILD_ROOT/var/spool/qmailscan/quarantine-attachments.db

# Install virus scanner subroutines
for s in sub-*.pl; do
	install $s $RPM_BUILD_ROOT/var/spool/qmailscan
	echo "1;" >> $RPM_BUILD_ROOT/var/spool/qmailscan/$s
done

%clean
rm -rf $RPM_BUILD_ROOT

%if %{with clamav}
%triggerin -- clamav
# Initialize the version file.
%{varqmail}/bin/qmail-scanner-queue -z

groups=$(id -Gn clamav)
if [[ "$groups" != *qscand* ]]; then
	# add qscand group to clamav
	QSCAND=$(/usr/bin/getgid qscand)
	if [ $? -eq 0 ]; then
		# NOTE:
		# not to wipe out other groups clamav could have,
		# we specify full list of groups
		%{_sbindir}/usermod -G ${groups// /,},qscand clamav &>/dev/null
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
%{varqmail}/bin/qmail-scanner-queue -z

# Initialize the perlscanner database.
%{varqmail}/bin/qmail-scanner-queue -g

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

%triggerin -- clamav
# Initialize the version file.
%{varqmail}/bin/qmail-scanner-queue -z

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
%attr(755,root,root) %{varqmail}/bin/qmail-scanner-queue.pl
%attr(6755,qscand,qscand) %{varqmail}/bin/qmail-scanner-queue

%dir %attr(750,qscand,qscand) /var/spool/qmailscan
%dir %attr(2750,qscand,qscand) /var/spool/qmailscan/tmp

%attr(700,qscand,qscand) /var/spool/qmailscan/archives
%attr(700,qscand,qscand) /var/spool/qmailscan/failed
%attr(700,qscand,qscand) /var/spool/qmailscan/quarantine
%attr(700,qscand,qscand) /var/spool/qmailscan/working

%attr(644,qscand,qscand) %config(noreplace) %verify(not size mtime md5) /var/spool/qmailscan/*.log
%attr(640,qscand,qscand) %verify(not size mtime md5) /var/spool/qmailscan/*.db

# scanner subs
/var/spool/qmailscan/*.pl

/var/spool/qmailscan/qmail-scanner-queue-version.txt
%config(noreplace) /var/spool/qmailscan/quarantine-attachments.txt

# reports of viruses per day
%dir /var/spool/qmailscan/reports
%attr(755,root,root) /var/spool/qmailscan/report.sh
