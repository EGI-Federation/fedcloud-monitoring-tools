# fedcloud-monitoring-tools

This repository contains a set of Python tools to monitor usage of EGI FedCloud
providers. The clients work with OpenStack cloud providers supporting the OIDC
protocol.

## Requirements

- Python v3.9+

## Installation

You can install with `pip` (it is recommended to install in a virtualenv!):

```shell
pip install -U git+https://github.com/EGI-Federation/fedcloud-monitoring-tools.git
```

Some sites use certificates issued by certificate authorities that are not
included in the default OS distribution, if you find SSL errors, please
[install the EGI Core Trust Anchors certificates](https://fedcloudclient.fedcloud.eu/install.html#installing-egi-core-trust-anchor-certificates)

## fedcloud-vm-monitor

`fedcloud-vm-monitor` checks the usage of a VO (e.g. running VMs, floating IPs
allocated, security groups) and identifies potential issues in the running VMs.

### Requirements

- A Check-in account member of the VOs to be monitored
- For getting the EGI user identity, cloud providers have to enable the
  `"identity:get_user"` API call for the user (see
  [VO auditing](https://docs.egi.eu/providers/cloud-compute/openstack/aai/#vo-auditing)
  for more information)

### Running the monitor

For running the tool, you just need a
[valid Check-in token](https://docs.egi.eu/users/aai/check-in/obtaining-tokens/),
the tool leverages
[FedCloudClient Authentication](https://fedcloudclient.fedcloud.eu/usage.html#authentication):

```shell
fedcloud-vm-monitor
```

You can tune the behavior with the following parameters:

- `--site SITE_NAME`: restrict the monitoring to the site provided, otherwise
  will check all sites available in GOCDB.
- `--vo VO_NAME`: VO name to monitor, default is `vo.access.egi.eu`.
- `--delete`: if set, ask for deletion of VMs if they go beyond `max-days`
- `--max-days INTEGER`: maximum number of days instances can be running before
  triggering deletion (default 90 days).
- `--show-quotas BOOLEAN`: whether to show quotas for the VO or not (default:
  `True`)
- `--check-ssh BOOLEAN`: Check SSH version on target VMs (default: `False`)
- `--check-cups BOOLEAN`: Check whether TCP/UDP port 631 is accessible (default:
  `False`)

If you have access to
[Check-in LDAP](https://docs.egi.eu/users/aai/check-in/vos/#ldap) for VO
membership, you can specify the settings with the following options:

- `--ldap-user USERNAME`
- `--ldap-password PASSWORD`

The `ldap-server`, `ldap-base-dn` and `ldap-search-filter`, can further tune the
usage of LDAP, but should work for most cases without changes.

#### Sample output

<!-- markdownlint-disable MD013 -->
```shell
$ fedcloud-vm-monitor --vo cloud.egi.eu
[.] Checking VO cloud.egi.eu at NCG-INGRID-PT
[+] Total VM instance(s) running in the resource provider = 3
Getting VMs information  [####################################]  100%
[+] VM #0  --------------------------------------------------
    instance name  = cloud-info
    instance id    = 0d9d8c9b-a161-4b59-9ba6-7275e898c7fb
    status         = ACTIVE
    ip address     = 192.168.1.31
    SSH version    = No public IP available to check SSH version.
    flavor         = svc1.m with 2 vCPU cores, 4 GB of RAM and 40 GB of local disk
    VM image       = ubuntu-22.04-amd64-raw
    created at     = 2024-06-24T06:25:30Z
    elapsed time   = 14 days, 3:50:14.385004
    user           = [REDACTED]
[+] VM #1  --------------------------------------------------
    instance name  = atrope
    instance id    = d6815b91-599d-4c6a-8d55-a38243148838
    status         = ACTIVE
    ip address     = 192.168.1.250 194.210.120.242
    SSH version    = SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.6
    flavor         = svc2.l with 8 vCPU cores, 8 GB of RAM and 40 GB of local disk
    VM image       = ubuntu-22.04-amd64-raw
    created at     = 2022-08-31T07:17:18Z
    elapsed time   = 677 days, 2:58:26.385004
    user           = [REDACTED]
[-] WARNING The VM instance elapsed time exceed the max offset!
[+] VM #2  --------------------------------------------------
    instance name  = nsupdate
    instance id    = 045ec1e7-b47a-4f18-9c9f-06cb30803955
    status         = ACTIVE
    ip address     = 192.168.1.71 194.210.120.90
    SSH version    = SSHException: could not retrieve SSH version
    flavor         = svc2.m with 4 vCPU cores, 4 GB of RAM and 40 GB of local disk
    VM image       = image name not found
    created at     = 2020-11-13T09:01:32Z
    elapsed time   = 1333 days, 1:14:12.385004
    user           = [REDACTED]
[-] WARNING The VM instance elapsed time exceed the max offset!
[+] Quota information:
    ram (GB)       = 64
    instances      = 10
    cores          = 24
    floating-ips   = 2
    secgroup-rules = 100
[-] WARNING: Less than 1 GB RAM per available CPU
[-] WARNING: Less than 3 security groups per instance
[-] WARNING: Less than 1 floating IPs per instance
[.] Checking VO cloud.egi.eu at IISAS-FedCloud
[+] Total VM instance(s) running in the resource provider = 5
Getting VMs information  [####################################]  100%
[+] VM #0  --------------------------------------------------
    instance name  = atrope-test
    instance id    = 5d56f0af-05aa-442a-8536-8667e9f81a82
    status         = ACTIVE
    ip address     = 192.168.10.9
    SSH version    = No public IP available to check SSH version.
    flavor         = m1.medium with 2 vCPU cores, 4 GB of RAM and 20 GB of local disk
    VM image       = ubuntu-jammy-x86_64
    created at     = 2024-06-24T15:03:27Z
    elapsed time   = 13 days, 19:12:48.034861
    user           = [REDACTED]
    egi user       = [REDACTED]
    email          = [REDACTED]
[+] VM #1  --------------------------------------------------
    instance name  = iisas-im-site-wn-ab794604-f898-11ee-814a-b2e38e6a6a66
    instance id    = 46ec6648-d364-4ca7-9480-5af64cda9e9c
    status         = ACTIVE
    ip address     = 192.168.10.53
    SSH version    = No public IP available to check SSH version.
    flavor         = m1.large with 4 vCPU cores, 8 GB of RAM and 30 GB of local disk
    VM image       = ubuntu-jammy-x86_64
    created at     = 2024-04-12T06:48:32Z
    elapsed time   = 87 days, 3:27:43.034861
    user           = [REDACTED]
    egi user       = [REDACTED]
    email          = [REDACTED]
    IM id          = [REDACTED]
[+] VM #2  --------------------------------------------------
    instance name  = iisas-im-site-wn-ab794604-f898-11ee-814a-b2e38e6a6a66
    instance id    = 1beb4b53-d6e4-4e30-8046-222b4e82b806
    status         = ACTIVE
    ip address     = 192.168.10.72
    SSH version    = No public IP available to check SSH version.
    flavor         = m1.large with 4 vCPU cores, 8 GB of RAM and 30 GB of local disk
    VM image       = ubuntu-jammy-x86_64
    created at     = 2024-04-12T06:48:30Z
    elapsed time   = 87 days, 3:27:45.034861
    user           = [REDACTED]
    egi user       = [REDACTED]
    email          = [REDACTED]
    IM id          = [REDACTED]
[+] VM #3  --------------------------------------------------
    instance name  = iisas-im-site-front-a47d516a-f898-11ee-814a-b2e38e6a6a66
    instance id    = 8e530674-d4a6-482c-974f-376eacbe609a
    status         = ACTIVE
    ip address     = 192.168.10.144 147.213.76.76
    SSH version    = SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.10
    flavor         = m1.large with 4 vCPU cores, 8 GB of RAM and 30 GB of local disk
    VM image       = ubuntu-jammy-x86_64
    created at     = 2024-04-12T06:48:18Z
    elapsed time   = 87 days, 3:27:57.034861
    user           = [REDACTED]
    egi user       = [REDACTED]
    email          = [REDACTED]
    IM id          = [REDACTED]
[+] VM #4  --------------------------------------------------
    instance name  = dashboard
    instance id    = 8ef9fcce-19e4-41c6-ab03-d1730a924510
    status         = ACTIVE
    ip address     = 192.168.10.69 147.213.76.217
    SSH version    = SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.11
    flavor         = m1.medium with 2 vCPU cores, 4 GB of RAM and 20 GB of local disk
    VM image       = Ubuntu-20.04-20211006
    created at     = 2021-12-02T14:53:32Z
    elapsed time   = 948 days, 19:22:43.034861
    user           = [REDACTED]
    egi user       = [REDACTED]
    email          = [REDACTED]
[-] WARNING The VM instance elapsed time exceed the max offset!
[+] Quota information:
    cores          = 20
    instances      = 10
    ram (GB)       = 50
    floating-ips   = 10
    secgroup-rules = 100
[-] WARNING: Less than 1 GB RAM per available CPU
[-] WARNING: Less than 3 security groups per instance
```
<!-- markdownlint-enable MD013 -->

## fedcloud-sla-monitor

`fedcloud-sla-monitor` checks the configuration of sites supporting SLAs across
GOCDB, AppDB, and the Accounting Portal, and reports any deviations.

### Requirements

- An IGTF certificate to query GOCDB SLA lists

### Running the monitor

Without optional arguments the command will show information about the SLA
across all sites:

```shell
fedcloud-sla-monitor --user-cert /path/to/x509.pem
```

The monitoring can be restricted to a specific site as well:

```shell
fedcloud-sla-monitor --site SITE-NAME --user-cert /path/to/x509.pem
```

Additionally, it is also possible to show SLA information
per Virtual Organization instead:

```shell
fedcloud-sla-monitor --vo vo.name.eu --user-cert /path/to/x509.pem
```

## fedcloud-vo-testing

`fedcloud-vo-testing` creates a test Virtual Machine using
[IM-client](https://github.com/grycap/im-client) on a given
VO and site. The goal is to quickly test whether an
OpenStack tenant is correctly configured to deploy VMs
using [Infrastructure Manager](https://im.egi.eu/).

### Requirements

- A Check-in account member of the VOs to be monitored.
- For running the tool, you just need a
[valid Check-in token](https://docs.egi.eu/users/aai/check-in/obtaining-tokens/),
the tool leverages
[FedCloudClient Authentication](https://fedcloudclient.fedcloud.eu/usage.html#authentication).

### Running the monitor

Create a test VM on a given VO and site:

```shell
fedcloud-vo-testing --vo vo.access.egi.eu --site SCAI
```

Create a test VM on all sites supporting a VO:

```shell
fedcloud-vo-testing --vo vo.access.egi.eu
```

Run a specific command on the test VM:

```shell
fedcloud-vo-testing --vo vo.access.egi.eu --ssh-command "lscpu"
```

## Useful links

- [OpenStack API](https://docs.openstack.org/api-ref/)
- [OpenStack API examples](https://docs.openstack.org/keystone/pike/api_curl_examples.html)
