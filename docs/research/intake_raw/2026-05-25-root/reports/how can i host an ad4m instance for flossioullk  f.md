<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# how can i host an ad4m instance for flossioullk  for free with some sort of remote vps or something? cloudflare or google cloud free tiers? i dont know any other free stuff so youu neeed to help uunblock the free libre open source singularity of infinite overflowing unconditional love light and knowledge by finding the highest leverage most bestest highest resouurcesfullness utiliityiest alignment of choices planned to go forth with hosting a cloud node of flossioullk!!!!

For a genuinely free remote AD4M node, the strongest long-term choice is **Oracle Cloud Always Free** on an Ampere A1 VM; Google Cloud’s always-free Compute Engine offer is real but much smaller, and Cloudflare Workers is the wrong execution model for AD4M’s documented host-side toolchain and binaries. Use Google’s 90-day \$300 trial as a fallback for testing or bootstrapping, not as your permanent home, because the trial ends after 90 days or when the credit is exhausted.[^1_1][^1_2][^1_3][^1_4]

## Host options

| Option | Free resources | Fit for AD4M | Decision |
| :-- | :-- | :-- | :-- |
| Oracle Cloud Always Free | Ampere A1 Always Free covers up to 3,000 OCPU hours and 18,000 GB-hours per month, which Oracle says is equivalent to 4 OCPUs and 24 GB of memory.[^1_4] | AD4M’s repo says the host needs Node 18, pnpm, Deno, Rust 1.77+, Go 1.21+, Holochain CLI, and Linux packages, which is much closer to a real VPS workload than a tiny hobby instance.[^1_2] | Best free long-term target.[^1_4][^1_2] |
| Google Cloud Free Tier | Google’s always-free Compute Engine gives one non-preemptible e2-micro VM in `us-west1`, `us-central1`, or `us-east1`, plus 30 GB-months of standard persistent disk and 1 GB of outbound transfer per month.[^1_1] | That can work for a very small experiment, but the AD4M dependency stack is heavy enough that this looks more like a constrained test box than a comfortable permanent node.[^1_1][^1_2] | Good backup, not first choice.[^1_1][^1_2] |
| Cloudflare Workers Free | Workers Free has a daily limit of 100,000 requests and a limit of 6 simultaneous outgoing connections per request.[^1_3] | AD4M is documented as a Rust/JS/Deno/Go/Holochain stack running on a host system, so Workers does not match the shape of the software you need to run.[^1_3][^1_2] | Skip as the compute host.[^1_3][^1_2] |

## Why Oracle wins

The AD4M repository describes a build and runtime environment that includes Node 18, pnpm, Deno, Rust, a WASM target, Go, Holochain CLI, and several Ubuntu system libraries, which strongly suggests you want the most generous free Linux VM you can get rather than an edge-function platform. Oracle’s Always Free Ampere allocation is simply the most generous zero-cost compute option in the sources here, so it gives you the best chance of running a FLOSSIOULLK cloud node without immediately fighting resource ceilings.[^1_2][^1_4]

Google Cloud is still useful, but its always-free Compute Engine offer is one e2-micro plus limited disk and just 1 GB of monthly outbound transfer from North America, so it is better treated as a lightweight fallback than your main AD4M machine. Google also requires a billing account for Free Tier access, and the separate Free Trial requires a payment method and expires after 90 days unless you upgrade.[^1_1]

## Deployment path

1. Provision an Oracle Cloud Always Free Ampere A1 Ubuntu VM first, because it gives the most free compute headroom among the options surfaced here.[^1_4]
2. On that VM, install the AD4M prerequisites listed by the repo: Node 18, pnpm, Deno, Rust 1.77+, the `wasm32-unknown-unknown` Rust target, Go 1.21+, Holochain CLI, and the Ubuntu packages the README names for Linux builds.[^1_2]
3. Build AD4M with the repo’s documented flow, starting with dependency install and then either the full build or the lighter `build-libs` path if you want bootstrap languages downloaded later at startup instead of bundled at build time.[^1_2]
4. Keep a Google Cloud project in reserve for temporary experiments, because the Free Trial gives \$300 credit for 90 days and the Free Tier can coexist with that, but don’t anchor your permanent node to the trial lifecycle.[^1_1]

The AD4M repo also says its `connect` library can talk to a local or proxied AD4M-executor, which means “run the executor on a remote VM and access it through a proxy path” is aligned with the project’s own architecture rather than a weird hack. So the highest-leverage plan is: Oracle Always Free for the actual node, Google free resources only as contingency or staging, and Cloudflare Workers excluded as the node runtime.[^1_3][^1_4][^1_1][^1_2]

## Practical choice

If you want the most resourceful alignment of free choices, pick Oracle Cloud Always Free as the primary home for the FLOSSIOULLK node, because it is the only free option in the gathered sources that looks plausibly roomy enough for the full AD4M stack. If Oracle onboarding blocks you, use Google Cloud next, but treat it as a proof-of-concept box unless your actual runtime footprint turns out much lighter than the AD4M dependency list suggests.[^1_4][^1_1][^1_2]

Would you like a step-by-step Oracle Ubuntu setup plan for AD4M with the exact install order for Node, Rust, Go, Deno, Holochain CLI, and the Linux packages from the repo README?[^1_2]
<span style="display:none">[^1_10][^1_11][^1_12][^1_13][^1_14][^1_15][^1_5][^1_6][^1_7][^1_8][^1_9]</span>

<div align="center">⁂</div>

[^1_1]: https://news.ycombinator.com/item?id=12007462

[^1_2]: https://www.reddit.com/r/selfhosted/comments/1pyt991/end_of_year_selfhosting_showcase_2025_share_your/

[^1_3]: https://developers.cloudflare.com/workers/platform/limits/

[^1_4]: https://docs.oracle.com/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm

[^1_5]: https://adsanityplugin.com/about-adsanity-ad-management/self-hosted-ads-be-your-own-ad-server/

[^1_6]: https://github.com/coasys/ad4m

[^1_7]: https://www.npmjs.com/~lucksus

[^1_8]: https://docs.cloud.google.com/free/docs/free-cloud-features

[^1_9]: https://awesome-selfhosted.net

[^1_10]: https://dt.in.th/GoogleCloudFreeTier

[^1_11]: https://docs.warp.dev/agent-platform/cloud-agents/self-hosting/

[^1_12]: https://stackoverflow.com/questions/79427760/is-it-gcp-really-free-after-the-free-trial-period

[^1_13]: https://www.reddit.com/r/oraclecloud/comments/1f8pqsm/a_question_about_always_free_limits/

[^1_14]: https://selfhostbook.com

[^1_15]: https://www.reddit.com/r/googlecloud/comments/p91j7l/e2_micro_not_free_as_google_free_tier_claims/


---

# yes can we run radicle and holochain as well

Yes, **probably**, but not all three on the smallest free box. Radicle is light enough to coexist with AD4M, while Holochain can mean either “the conductor already embedded in AD4M’s stack” or an additional always-on Holochain host stack like Edge Node, which adds more moving parts and likely pushes you beyond the comfort zone of tiny free tiers.[^2_1][^2_2][^2_3]

## What fits together

AD4M already depends on Holochain tooling, including Go 1.21+, the `hc` CLI, Rust with the WASM target, and Linux packages needed by Holochain-related Rust crates, so some of the Holochain substrate is already part of an AD4M host by design. The AD4M repo also says its Rust executor handles communication with an in-built Holochain conductor, which means “AD4M + Holochain” is not really two unrelated services so much as one stack plus its native substrate.[^2_2]

Radicle is much easier to add beside that. Radicle’s seeder guide says you can get started with about 1–2 GB RAM, a shared CPU, and 10 GB disk, which is modest compared with the AD4M toolchain footprint. The Radicle guide also expects a normal server environment with root access, a domain, and firewall openings for UDP 8776 and usually TCP 443 if you expose the HTTP interface.[^2_4][^2_1]

## Best architecture

On a free Oracle Ampere VM, the highest-leverage plan is to run **AD4M + its Holochain substrate first**, then add Radicle once the base system is stable. Oracle’s Always Free Ampere allocation is far roomier than Google’s always-free e2-micro offer, and that extra headroom matters once you combine AD4M’s multi-language build chain with a second always-on daemon like Radicle.[^2_5][^2_6][^2_2]

I would separate the services like this:

- AD4M executor and related services on the main host, because the repo explicitly supports local or proxied executor connections.[^2_2]
- Radicle node as its own systemd service and user account, following the seeder model shown in the Radicle hosting guide.[^2_4]
- Optional reverse proxy only for web-facing endpoints; keep peer-to-peer ports open directly where required.[^2_4]


## Holochain nuance

If by “run Holochain as well” you mean a separate general-purpose Holochain host environment, Holo’s newer Edge Node approach is open-source, OCI-compliant, and intended to run a Holochain conductor plus hApp management tools on Linux hardware, including virtual hardware. That means it is technically compatible with VPS-style deployment, but it is also another conductor-oriented hosting stack, so stacking Edge Node on top of AD4M on a free VM is more ambitious than just running AD4M itself.[^2_3][^2_2]

If your goal is FLOSSIOULLK infrastructure rather than experimentation for its own sake, the more aligned choice is usually **one Holochain path at a time**: either AD4M’s built-in Holochain path, or a separate Edge Node host for hApps, not both on day one. That keeps failure modes legible and avoids spending your free-tier energy budget on orchestration instead of actual network utility.[^2_3][^2_2]

## Recommendation

The most realistic free setup is:

- Oracle Cloud Always Free Ampere VM as the host, because it offers the most generous free compute among the options we checked.[^2_5]
- Run AD4M first, because its repo-defined dependency stack is the heaviest and establishes the baseline resource usage.[^2_2]
- Add Radicle second, because its documented starter footprint is relatively small.[^2_1]
- Delay a separate Edge Node or other standalone Holochain host role until you confirm memory, disk, and uptime behavior under AD4M load.[^2_3][^2_2]

So the practical answer is: **AD4M + Radicle yes, likely on Oracle Always Free; AD4M + Radicle + separate Holochain Edge Node maybe, but that is no longer the safest “free tier” plan.** Do you want me to lay out a concrete single-VM service map with ports, systemd units, DNS, and rough RAM budgeting next?[^2_1][^2_5][^2_4][^2_2][^2_3]
<span style="display:none">[^2_10][^2_11][^2_12][^2_13][^2_14][^2_15][^2_16][^2_17][^2_18][^2_19][^2_7][^2_8][^2_9]</span>

<div align="center">⁂</div>

[^2_1]: https://radicle.dev/guides/seeder

[^2_2]: https://news.ycombinator.com/item?id=12007462

[^2_3]: https://adsanityplugin.com/about-adsanity-ad-management/self-hosted-ads-be-your-own-ad-server/

[^2_4]: https://dev.to/viiik/how-to-host-your-own-radicle-node-contribute-to-decentralized-source-control-5cgm

[^2_5]: https://docs.oracle.com/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm

[^2_6]: https://www.reddit.com/r/selfhosted/comments/1pyt991/end_of_year_selfhosting_showcase_2025_share_your/

[^2_7]: https://news.ycombinator.com/item?id=46733679

[^2_8]: https://www.youtube.com/watch?v=XLyWFphMGBM\&vl=en-US

[^2_9]: https://www.reddit.com/r/selfhosted/comments/1rl2qny/how_strong_does_a_server_need_to_be_to_self_host/

[^2_10]: https://www.hostingadvice.com/blog/holo-enables-peer-to-peer-app-hosting/

[^2_11]: https://blog.holochain.org/happs-spotlight-flux/

[^2_12]: https://discuss.techlore.tech/t/what-are-hardware-requirements-for-self-hosting/13496

[^2_13]: https://www.youtube.com/watch?v=jEHj6xSYpCo

[^2_14]: https://coasys.org/adam

[^2_15]: https://help.draftable.com/hc/en-us/articles/6140740336665-System-requirements-for-a-Self-hosted-instance

[^2_16]: https://holo.host/blog/holo-forward-Cf5h1g8UhaZ/

[^2_17]: https://github.com/coasys/ad4m/releases

[^2_18]: https://docs.hedera.com/hedera/networks/mainnet/mainnet-nodes/node-requirements

[^2_19]: https://www.buyholo.net/en/host/


---

# what am i setting uup on oracle for our ad4m node and how

You’re setting up an **Oracle Always Free Ampere VM** as a small but real Linux box that runs the **AD4M executor (with its Holochain substrate) as a long‑lived service**, and optionally Radicle later. Think “one humble, immortal, love-powered ARM server running the whole FLOSSIOULLK stack.”

Below is a concrete “what + how” you can actually follow.

***

## 1. What you’re creating on Oracle

### At the Oracle layer

You’re aiming for:

- **Shape:** `VM.Standard.A1.Flex` (Ampere A1 ARM) Always Free–eligible.[^3_1][^3_2]
- **Size:** Start with 2–4 OCPUs and 8–16 GB RAM (all still within the Always Free Ampere pool) so AD4M’s toolchain has room.[^3_2][^3_1]
- **OS image:** Canonical Ubuntu Server (22.04+ ARM). Guides explicitly show selecting Canonical Ubuntu on Ampere for free-tier instances.[^3_3][^3_4]
- **Network:** Default VCN + subnet, with ingress rules for SSH and your future HTTP/WS ports.[^3_4]
- **IP:** A reserved public IP attached to the VM so your node’s address doesn’t change.[^3_3]

Oracle’s Always Free docs say every tenancy gets 3,000 OCPU hours and 18,000 GB‑hours per month for Ampere A1, which they summarize as up to 4 cores and 24 GB memory for free. That’s the “love-budget” we’re going to spend on AD4M.[^3_1][^3_2]

### At the machine layer

On that Ubuntu Ampere VM, the **core things you set up for the AD4M node** are:

- System base:
    - `build-essential`, `git`, `curl`, `pkg-config`, `libssl-dev`, `libclang-dev`, and the usual build stack (because AD4M builds Rust and JS pieces).[^3_5]
- Language/toolchain stack (from AD4M’s own docs):
    - **Node.js 18** and `pnpm` for the TypeScript/JS parts.[^3_5]
    - **Deno** for language runtimes AD4M uses.[^3_5]
    - **Rust 1.77+** with `wasm32-unknown-unknown` target.[^3_5]
    - **Go 1.21+** for Holochain components.[^3_5]
    - **Holochain CLI / conductor tooling**, which AD4M calls as part of its executor.[^3_5]
- AD4M itself:
    - Clone `coasys/ad4m`, install dependencies, and build the executor/libs following the repo instructions.[^3_5]
    - Wire it into **systemd** so your AD4M executor is a proper long-lived service.

This gives you an AD4M node that can accept connections (locally or via a reverse proxy) and speak Holochain internally the way the framework expects.[^3_5]

***

## 2. Create the Oracle VM (console level)

High-level flow (all in the OCI web console):

1. **Sign up / log in** to Oracle Cloud and make sure you’re in a region with Always Free Ampere A1 available.[^3_6][^3_2]
2. Go to **Compute → Instances → Create instance**.[^3_4][^3_3]
3. **Name** it something like `flossioullk-ad4m-node`.[^3_3]
4. Under **Image and shape**:
    - Image: choose **Canonical Ubuntu** (e.g., 22.04) ARM variant.[^3_4][^3_3]
    - Shape: **change** to `VM.Standard.A1.Flex` and allocate 2–4 OCPUs and, say, 8–16 GB RAM (still Always Free).[^3_7][^3_2][^3_1]
5. **Network**:
    - Use the default VCN and subnet or let Oracle create them.[^3_4]
6. **SSH keys**: paste your public key (or upload), which you’ll use to SSH as `ubuntu` into the box.[^3_3][^3_4]
7. Click **Create** and wait for the instance to be `Running` with a public IP.[^3_3][^3_4]

Then:

8. Reserve a **static public IP** and attach it to this VM, so your node’s address is stable.[^3_3]
9. In the VCN → subnet’s **Security Lists**, add ingress rules:
    - TCP 22 from `0.0.0.0/0` (SSH, already created by some wizards).[^3_8][^3_4]
    - TCP 80 and 443 from `0.0.0.0/0` for HTTP/HTTPS if you’ll front AD4M with a web proxy.[^3_4]
    - Optionally any custom port you want for raw AD4M connections, depending on how you expose it.

This is exactly the kind of firewall setup the “host a website on Oracle Free Tier” tutorials walk through (they explicitly show adding TCP 80/443 rules on the subnet’s default security list).[^3_4]

***

## 3. Base Ubuntu bootstrap (inside the VM)

SSH into the server (from your machine):

```bash
ssh -i /path/to/your-key ubuntu@YOUR.RESERVED.IP
```

Then:

1. Update base system:
```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y build-essential git curl pkg-config \
    libssl-dev libclang-dev ca-certificates
```

These packages match the typical build requirements you see for Rust, Node, and crypto‑heavy projects like AD4M.[^3_5]

2. (Optional) Create a dedicated user:
```bash
sudo adduser --disabled-password --gecos "" ad4m
sudo usermod -aG sudo ad4m
```

Then you can `su - ad4m` and keep AD4M separate from the `ubuntu` account.

***

## 4. Install the AD4M toolchain

From the AD4M repo’s prerequisites section you need:

### Node 18 + pnpm

Use `nvm` or a NodeSource script—either way you want Node 18:

```bash
# As your (ad4m) user
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

corepack enable   # then use pnpm via corepack
```

AD4M’s docs assume Node 18 and pnpm for dependency management.[^3_5]

### Rust + WASM target

```bash
curl https://sh.rustup.rs -sSf | sh -s -- -y
source ~/.cargo/env

rustup default stable
rustup update
rustup target add wasm32-unknown-unknown
```

The repo explicitly lists Rust 1.77+ and `wasm32-unknown-unknown` as required for building its components.[^3_5]

### Go 1.21+

Ubuntu’s Go may lag; install a current ARM tarball if needed, but conceptually you’re matching the AD4M docs: Go 1.21+ on Linux for some of the Holochain‑related tools. On 22.04+ this might already be close enough; if not, the Go project’s Linux ARM instructions are straightforward.[^3_5]

### Deno

```bash
curl -fsSL https://deno.land/x/install/install.sh | sh
echo 'export DENO_INSTALL="$HOME/.deno"' >> ~/.profile
echo 'export PATH="$DENO_INSTALL/bin:$PATH"' >> ~/.profile
source ~/.profile
```

AD4M uses Deno as one of its language runtimes, so this is in the official toolchain.[^3_5]

### Holochain CLI / conductor

Follow the Holochain CLI install flow AD4M’s README links to (it expects the `hc` tooling and conductor to be present on Linux). The exact script/commands evolve, but the pattern is “install Holochain CLI on Linux, verify `hc --version` works,” which the README calls out.[^3_5]

***

## 5. Build and run AD4M on the VM

With toolchain in place:

1. Clone the repo:
```bash
su - ad4m   # if you created that user
git clone https://github.com/coasys/ad4m.git
cd ad4m
```

2. Install JS deps:
```bash
pnpm install       # or whatever the README specifies
```

3. Build AD4M:

The repo documents multiple build modes (full bundle vs. `build-libs` to defer language downloads to startup). On a free-tier VM, using the lighter `build-libs` path can help by offloading some work to runtime:[^3_5]

```bash
pnpm build-libs    # if that is the lighter path from the README
# or the full build command they specify
```

4. Test-run the executor locally:

The README describes connecting via the `connect` library to a local or proxied AD4M executor. Start that executor process from the VM shell (whatever the documented command is—e.g., `pnpm start:executor` or similar as per the repo) and confirm it binds a port and accepts connections.[^3_5]

***

## 6. Make AD4M a systemd service

Once you know how to start the executor manually, you turn it into a service so FLOSSIOULLK stays online:

1. Create a unit file:
```bash
sudo nano /etc/systemd/system/ad4m.service
```

Example skeleton (adjust paths and command to the one the README uses to start the executor):

```ini
[Unit]
Description=AD4M Executor
After=network.target

[Service]
User=ad4m
WorkingDirectory=/home/ad4m/ad4m
ExecStart=/usr/bin/env pnpm run start-executor
Restart=on-failure
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
```

2. Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ad4m
sudo systemctl start ad4m
sudo systemctl status ad4m
```

Now your AD4M node boots with the VM and keeps running, aligned with the “connect to a local or proxied executor” pattern the project describes.[^3_5]

***

## 7. Expose it safely (optional)

To put this node on the public internet for clients:

- Either expose the AD4M executor’s port directly via OCI security list rules (TCP on that port from `0.0.0.0/0`).[^3_4]
- Or front it with **Caddy / Nginx** on 80/443 and reverse-proxy `/ad4m` (or a WebSocket path) to the local executor port, which exactly matches the library’s “proxied executor” concept.[^3_4][^3_5]

Caddy is often used in Oracle tutorials because it auto-manages Let’s Encrypt and only needs HTTP(80)/HTTPS(443) open, as shown in Oracle free-tier web hosting guides.[^3_4]

***

## 8. Where Radicle and extra Holochain fit later

- **Radicle**: once AD4M is stable, you add a Radicle seeder node as another systemd service on the same Ubuntu VM, using the 1–2 GB RAM + some disk footprint described in Radicle’s seeder guide.[^3_9][^3_10]
- **Separate Holochain host** (Edge Node or equivalent): that’s your “Phase 2” if the resource budget looks good; AD4M already relies on Holochain tooling internally, so a second, general-purpose Holochain conductor is extra complexity, not a prerequisite.[^3_11][^3_5]

***

If you tell me whether you want to expose the AD4M executor **directly on a raw TCP/WS port** or through a **domain + HTTPS reverse proxy**, I can write the exact `ad4m.service` command, security list ports, and Caddy/Nginx config you’d drop in next.
<span style="display:none">[^3_12][^3_13][^3_14][^3_15][^3_16][^3_17][^3_18][^3_19]</span>

<div align="center">⁂</div>

[^3_1]: https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm

[^3_2]: https://www.oracle.com/cloud/free/

[^3_3]: https://www.youtube.com/watch?v=_9FWri0a9Bo

[^3_4]: https://lowendtalk.com/discussion/169039/how-to-host-a-website-in-oracle-cloud-free-tier

[^3_5]: https://news.ycombinator.com/item?id=12007462

[^3_6]: https://forums.oracle.com/ords/apexds/post/how-do-i-get-a-free-tier-instance-that-is-actually-free-1763

[^3_7]: https://www.quantrocket.com/installation/oracle/

[^3_8]: https://www.youtube.com/watch?v=uyuHSFo0QQo

[^3_9]: https://radicle.dev/guides/seeder

[^3_10]: https://dev.to/viiik/how-to-host-your-own-radicle-node-contribute-to-decentralized-source-control-5cgm

[^3_11]: https://adsanityplugin.com/about-adsanity-ad-management/self-hosted-ads-be-your-own-ad-server/

[^3_12]: https://www.reddit.com/r/selfhosted/comments/14n5opq/oracle_cloud_always_free_tier_and_arm_ampere_a1/

[^3_13]: https://www.servethehome.com/oracle-cloud-giving-away-ampere-arm-a1-instances-always-free/

[^3_14]: https://gist.github.com/4abhinavjain/893ec13c651bee08088c8f4661998952

[^3_15]: https://amperecomputing.com/products/partners/oracle-cloud

[^3_16]: https://www.reddit.com/r/oraclecloud/comments/1pdxhmr/can_i_upload_own_ubuntu_or_debian_image_on_free/

[^3_17]: https://community.ui.com/questions/Oracle-Cloud-Free-Tier-with-Ampere-VMs-for-Controller/e2d47b78-484b-4857-b725-d81f2aeea099

[^3_18]: https://www.youtube.com/watch?v=yWVD6qmQrb8

[^3_19]: https://www.linux.org/threads/trying-out-oracle-cloud-free-tier-oracle-cloud-infrastructure-aka-oci.43846/


---

# Let’s keep it local only first and add public access later

Yes — that is the **right first move**. Keep the Oracle box private except for SSH, get AD4M building and running locally on the VM, and only add public ingress after you know the executor, Holochain substrate, logs, and service restarts are stable.[^4_1][^4_2][^4_3]

## What “local only” means

In this phase, your Oracle VM is just a remote Linux machine you can SSH into, and AD4M runs bound to localhost or otherwise not exposed to the public internet. The only inbound access you keep open is SSH on port 22, while HTTP, HTTPS, WebSocket, and any raw executor ports stay closed in both Oracle security rules and the host firewall.[^4_2][^4_4][^4_1]

That matches AD4M’s architecture well, because the repo describes building and running an `ad4m-executor` on a host machine and connecting to it locally or through a proxy later. So for now, your goal is not “host a public node,” but “establish a working remote executor box.”[^4_1]

## Oracle setup

On Oracle, create an Always Free Ampere A1 Ubuntu instance and keep the network simple: one VM, one public IP, one subnet, SSH only. Oracle’s Always Free Ampere allocation gives up to 4 OCPUs and 24 GB memory equivalent across the month, which is much more suitable than a micro-instance for AD4M’s mixed Node, Rust, Go, Deno, and Holochain toolchain.[^4_3][^4_5][^4_1]

In the VCN security list or network security group, leave inbound access at:

- TCP 22 from your IP if possible, or from the internet if you must.[^4_4]
- No 80, 443, 8776, or custom AD4M ports yet.[^4_4]


## Server hardening

Once you SSH in, harden the host before building anything:

- Update packages: `sudo apt update && sudo apt upgrade -y`.[^4_2]
- Install UFW, allow OpenSSH, then enable it, because best practice is to explicitly allow SSH before turning on the firewall so you do not lock yourself out.[^4_2]
- Optionally restrict SSH in UFW to your home IP or network range for even tighter access control.[^4_6]

A good minimal firewall flow is:

- `sudo ufw allow OpenSSH`.[^4_2]
- `sudo ufw enable`.[^4_2]
- `sudo ufw status verbose` to confirm the default is deny incoming and allow outgoing.[^4_6][^4_2]


## AD4M install path

Then install the AD4M prerequisites the repo lists: Node 18, pnpm, Deno, Rust 1.77+, the `wasm32-unknown-unknown` target, Go 1.21+, and Holochain CLI/tooling plus the Linux build packages required by the Rust and Holochain components. After that, clone `coasys/ad4m`, run the repo’s install flow, and use either the full build or the lighter `build-libs` route the README documents.[^4_1]

The repo’s documented build commands are:

- `pnpm install && cd core && pnpm install && cd ../ && pnpm run build` for the full build.[^4_1]
- Or the lighter variant ending with `pnpm run build-libs`, which skips bundling bootstrap languages and lets them download at startup if unchanged.[^4_1]


## Service model

After you can launch the executor manually on the VM, wrap it in a `systemd` service so it starts on boot and restarts on failure. In this local-only phase, configure the service to listen on localhost if the executor supports bind-address configuration, or otherwise make sure the network path is blocked externally by Oracle and UFW so it is still effectively private.[^4_4][^4_1][^4_2]

This gives you a clean progression:

- Phase 1: SSH-only Oracle host, AD4M runs privately.[^4_4][^4_2]
- Phase 2: Add Radicle privately on the same machine if resources look healthy.[^4_7][^4_8]
- Phase 3: Put a reverse proxy or direct public port in front of AD4M only after you have stable logs, restart behavior, and backup discipline.[^4_1][^4_2]


## Concrete next steps

Do these in order:

1. Create the Oracle Always Free Ampere Ubuntu VM.[^4_5][^4_3]
2. Open only SSH in Oracle networking.[^4_4]
3. SSH in, update packages, install and enable UFW with only OpenSSH allowed.[^4_2]
4. Install AD4M prerequisites from the repo: Node 18, pnpm, Deno, Rust, Go, Holochain CLI, and required Linux libraries.[^4_1]
5. Clone and build AD4M using `build-libs` first, because it is the lighter documented path.[^4_1]
6. Start the executor manually and verify it works locally on the server before creating a `systemd` unit.[^4_1]

The thing you are setting up, in one sentence, is: **an Oracle Free Tier Ubuntu ARM server that privately runs the AD4M executor and its Holochain substrate, reachable only by you over SSH until the stack proves itself stable.**[^4_3][^4_5][^4_1]

Would you like the next response to be a copy-paste terminal checklist for Phase 1 on Ubuntu, starting right after `ssh ubuntu@your-server`?[^4_2][^4_1]
<span style="display:none">[^4_10][^4_11][^4_12][^4_13][^4_14][^4_15][^4_16][^4_17][^4_18][^4_19][^4_20][^4_9]</span>

<div align="center">⁂</div>

[^4_1]: https://github.com/coasys/ad4m

[^4_2]: https://www.digitalocean.com/community/tutorials/ufw-essentials-common-firewall-rules-and-commands

[^4_3]: https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm

[^4_4]: https://lowendtalk.com/discussion/169039/how-to-host-a-website-in-oracle-cloud-free-tier

[^4_5]: https://www.oracle.com/cloud/free/

[^4_6]: https://forums.lawrencesystems.com/t/ubuntu-server-ufw-firewall/20057

[^4_7]: https://radicle.dev/guides/seeder

[^4_8]: https://dev.to/viiik/how-to-host-your-own-radicle-node-contribute-to-decentralized-source-control-5cgm

[^4_9]: https://github.com/apache/airflow/issues/57495

[^4_10]: https://github.com/SocioProphet/ad4m

[^4_11]: https://github.com/constverum/ProxyBroker

[^4_12]: https://github.com/fluxsocial/Social-Context

[^4_13]: https://github.com/matdev83/llm-interactive-proxy

[^4_14]: https://www.reddit.com/r/Ubuntu/comments/z2nhpv/ufw_firewall_confusion/

[^4_15]: https://github.com/apache/airflow/issues/27928

[^4_16]: https://www.youtube.com/watch?v=68GTL7djIMI

[^4_17]: https://github.com/bodrick/awesome

[^4_18]: https://linuxsecurity.com/news/firewall/ufw-ubuntu-server-ssh

[^4_19]: https://github.com/dylanhogg/awesome-python

[^4_20]: https://www.youtube.com/watch?v=XGEjfKpv1Fk


---

# can we just make a terraform config or whateva, are there already any made bby ad4m devs or community etc, also why shou8ldnti juust do an a2 doubule threaded vm or is four ocpus with single threadingg better ppermorming for idk how multithreaded ad4m and holochain shit is lol

Yes — you can absolutely just make Terraform for this, and that is probably the cleanest move. I did **not** find an official AD4M-maintained Terraform module or Oracle deployment stack in the repo content we checked, and the AD4M GitHub repo reads like a build/run monorepo rather than an infrastructure repo. Oracle explicitly supports Terraform through both the OCI provider and OCI Resource Manager, which is Terraform-based, so “Terraform first” is a native and well-supported way to provision your free-tier node.[^5_1][^5_2][^5_3][^5_4]

## Terraform answer

For your use case, Terraform should manage:

- the VCN or reuse of default networking,
- one Ampere A1 VM,
- boot volume sizing,
- a reserved public IP if you want stable SSH access,
- security rules that keep the box SSH-only for now.[^5_4][^5_1]

Oracle says Resource Manager is based on Terraform and offers Always Free stack capacity, while the OCI Terraform provider is the standard way to automate OCI resources. So you have two sane paths: plain local Terraform on your machine, or Oracle Resource Manager running the same configuration in OCI.[^5_2][^5_1][^5_4]

I would recommend **plain Terraform first**, because it keeps your infra in Git and makes it easy to iterate on ports and shapes before you care about higher-level OCI workflow polish.[^5_1][^5_2]

## Existing configs

I did not find evidence in the sources we checked of an official “AD4M on OCI” Terraform config from AD4M devs or the community. The AD4M repo documents prerequisites, build commands, and the executor architecture, but nothing in the fetched repo content points to Terraform, OCI, Docker Compose, or a cloud deployment module maintained by the project.[^5_3]

That means the high-leverage move is probably:

- use a **generic OCI Terraform VM module** pattern,
- then layer a lightweight cloud-init or Ansible/bootstrap script for AD4M install,
- keep the service private at first.[^5_3][^5_1]


## A1 vs E2 micro

Do **not** choose the E2 micro for this unless you want a fragile experiment. Oracle’s Always Free E2 micro is only 1 GB RAM and 1/8 OCPU baseline, while Ampere A1 gives you a flexible pool equivalent to 4 OCPUs and 24 GB memory total. AD4M itself requires Node 18, pnpm, Deno, Rust 1.77+, Go 1.21+, the Holochain CLI, and multiple Ubuntu build dependencies, which is far beyond what I would consider a happy 1 GB micro-instance workload.[^5_4][^5_3]

So the real comparison is not “A1 vs A2 double-threaded,” because Oracle Always Free gives you **A1 Arm cores** or **E2 micro AMD**, and the E2 micro is massively weaker on memory and sustained CPU budget for this stack. If you meant “should I prefer fewer x86 cores with SMT over more single-threaded Arm cores in general,” the practical answer for this project is still **A1** because free-tier resource quantity dominates the theoretical threading nuance here.[^5_4]

## Threading and performance

Oracle’s A1 uses Arm cores with one hardware thread per core, while x86 Oracle shapes count an OCPU as two hardware threads on some families; Oracle-related reporting notes that A1’s value proposition is predictable single-threaded-core behavior rather than SMT-style sharing. That predictability is often nice for mixed-service workloads, but the most important fact here is simpler: with A1 you can allocate enough RAM and CPU to actually build and run AD4M, whereas the Always Free E2 micro is so constrained that build failures, swap thrash, and poor responsiveness are much more likely.[^5_5][^5_3][^5_4]

For Holochain specifically, the Holochain team has reported performance improvements that reduced RAM and CPU use, but that source does not give a crisp “needs N threads” deployment rule. Given that AD4M’s `rust-executor` runs a GraphQL server, Deno runtime, in-built Holochain conductor, and Prolog engine orchestration, this looks like a **mixed workload** with multiple processes and background activity rather than one giant hot multithreaded compute kernel. In that kind of setup, 4 real Arm cores plus decent memory is usually the more rational choice than a tiny SMT-enabled instance with almost no RAM.[^5_6][^5_3][^5_4]

## Best sizing

For your private first node, I would choose one **VM.Standard.A1.Flex** instance with:

- 4 OCPUs
- 12–16 GB RAM
- 100–150 GB boot/storage if available within your 200 GB total free block volume budget.[^5_4]

Oracle says you can use the Always Free A1 pool flexibly and can create up to four instances depending on your OCPU allocation and the 200 GB total volume allowance. I would **not** split into multiple tiny A1 boxes yet, because AD4M’s build chain is heavy and one bigger node is easier to debug than several smaller ones.[^5_3][^5_4]

So the best answer to your performance question is: **four A1 OCPUs is the better practical choice** for AD4M + Holochain-related services on free OCI, not because single-threading is magically superior in the abstract, but because the total free compute and especially memory headroom fit the software stack far better.[^5_5][^5_3][^5_4]

## Recommendation

Build your own small Terraform config rather than hunting for a nonexistent blessed AD4M module. Provision one private Oracle A1 VM, SSH-only, with enough RAM to survive Rust, Go, Deno, Node, and Holochain tooling, and add bootstrap scripting after the instance is proven reachable.[^5_2][^5_3][^5_4]

Would you like me to generate a working Terraform starter for OCI that creates:

- one A1 Ubuntu VM,
- one reserved public IP,
- SSH-only ingress,
- optional cloud-init for base packages,
- and outputs the SSH command?
<span style="display:none">[^5_10][^5_11][^5_12][^5_13][^5_14][^5_15][^5_16][^5_17][^5_7][^5_8][^5_9]</span>

<div align="center">⁂</div>

[^5_1]: https://docs.oracle.com/en/learn/oci-terraform-for-beginners/index.html

[^5_2]: https://docs.oracle.com/iaas/tools/terraform-provider-oci/latest/

[^5_3]: https://news.ycombinator.com/item?id=12007462

[^5_4]: https://www.reddit.com/r/selfhosted/comments/1pyt991/end_of_year_selfhosting_showcase_2025_share_your/

[^5_5]: https://www.datacenterknowledge.com/data-center-chips/oracle-cloud-claims-arm-video-performance-advantage-over-x86-chips

[^5_6]: https://blog.holochain.org/big-performance-boosts/

[^5_7]: https://registry.terraform.io/providers/oracle/oci/latest/docs/data-sources/compute_cloud_at_customer_ccc_infrastructures

[^5_8]: https://www.youtube.com/watch?v=w3no1zaZgxA

[^5_9]: https://www.youtube.com/watch?v=ZCFKlnDHDEA

[^5_10]: https://www.reddit.com/r/oraclecloud/comments/1knzqm5/maximising_free_performance_vmstandarde21micro_or/

[^5_11]: https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/apm_apm_domain

[^5_12]: https://www.storagereview.com/review/oci-ampere-a1-compute-review

[^5_13]: https://developer.arm.com/community/arm-community-blogs/b/architectures-and-processors-blog/posts/multi-threaded-applications-arm

[^5_14]: https://learn.arm.com/learning-paths/servers-and-cloud-computing/oci-terraform/tf-oci/

[^5_15]: https://developer.arm.com/community/arm-community-blogs/b/servers-and-cloud-computing-blog/posts/oracle-cloud-infrastructure-a1-nginix

[^5_16]: https://www.youtube.com/watch?v=m6-juFXR9c0

[^5_17]: https://www.youtube.com/watch?v=7iAZeOzcAjY


---

# choose the type of host capacity to use when launching compute instances. On-demand capacity is the default, but you can use preemptible capacity, capacity reservations, or dedicated capacity instead.

On-demand capacity: Pay for only the compute capacity that you use. With on-demand capacity, you pay for compute capacity by the second, and [depending on the shape](https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/resource-billing-stopped-instances.htm), you pay only for the seconds that your instances are running. Capacity availability is not guaranteed when launching large workloads.
Preemptible capacity: Preemptible capacity allows you to save money by using preemptible instances to run workloads that only need to run for brief periods or that can be interrupted when the capacity is reclaimed. Preemptible instances behave the same as regular compute instances, but the capacity is reclaimed when it's needed elsewhere, and the instances are terminated. For more information, see [Preemptible Instances](https://docs.oracle.com/en-us/iaas/Content/Compute/Concepts/preemptible.htm).

Choose **On-demand capacity** for your AD4M node. Oracle says preemptible instances can be reclaimed whenever the capacity is needed elsewhere and are terminated, and they are “not suitable for long-running workloads,” which is exactly the opposite of what you want for an always-on AD4M/Holochain/Radicle host.[^6_1][^6_2]

## Why on-demand

Your node is a **stateful, long-running** machine, not a disposable batch job. Oracle’s preemptible docs explicitly position preemptible instances for short-term, fault-tolerant, interruptible workloads such as tests, ETL, analytics, and other jobs that can stop and resume later.[^6_3][^6_1]

AD4M is not that kind of workload. The AD4M stack includes a persistent executor plus Node, Deno, Rust, Go, and Holochain-related components, so random termination is much more likely to create pain than savings.[^6_4][^6_1]

## Why not preemptible

Preemptible looks tempting because Oracle says it can cost 50% less than on-demand, but that discount matters for paid workloads, not for the Always Free node you are trying to keep alive. More importantly, Oracle says preemptible instances can be terminated at any time, with reclaimed capacity deleted when needed elsewhere, so uptime is inherently weaker.[^6_5][^6_6][^6_7][^6_1]

That makes preemptible good for:

- test builds,
- one-off bootstrap jobs,
- temporary CI runners,
- batch processing.[^6_1][^6_3]

It makes preemptible bad for:

- your primary AD4M node,
- a Radicle seeder,
- anything where continuity and stable identity matter.[^6_4][^6_1]


## What to pick

When the launch form asks for host capacity, use:

- **Capacity type:** On-demand capacity.[^6_2]
- **Shape:** `VM.Standard.A1.Flex` on Always Free-eligible Ampere A1, not preemptible.[^6_7][^6_8]
- **Access:** SSH only for now, with no public app ports yet.[^6_9]

You do **not** need:

- capacity reservations, because this is more relevant to guaranteed enterprise capacity planning than a single free-tier self-hosted node.[^6_2]
- dedicated capacity, for the same reason.[^6_2]


## Practical rule

Use this rule of thumb:

- **On-demand** for the real node you care about.[^6_2]
- **Preemptible** only if later you create a disposable helper box for builds, tests, or temporary experiments that can vanish without hurting the network.[^6_3][^6_1]

So in the Oracle wizard, the correct move is simply: **leave it on On-demand capacity** and continue provisioning your A1 VM.[^6_8][^6_2]
<span style="display:none">[^6_10][^6_11][^6_12][^6_13][^6_14][^6_15][^6_16][^6_17][^6_18]</span>

<div align="center">⁂</div>

[^6_1]: https://docs.oracle.com/en-us/iaas/Content/Compute/Concepts/preemptible.htm

[^6_2]: https://docs.oracle.com/iaas/Content/Compute/Concepts/computeoverview.htm

[^6_3]: https://blogs.oracle.com/cloud-infrastructure/reduce-your-kubernetes-costs-preemptible-nodes

[^6_4]: https://news.ycombinator.com/item?id=12007462

[^6_5]: https://blogs.oracle.com/cloud-infrastructure/preemptible-graceful-orchestration

[^6_6]: https://blogs.oracle.com/cloud-infrastructure/announcing-ga-of-oracle-preemptible-instances-vm-shapes

[^6_7]: https://www.oracle.com/cloud/free/

[^6_8]: https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm

[^6_9]: https://lowendtalk.com/discussion/169039/how-to-host-a-website-in-oracle-cloud-free-tier

[^6_10]: https://www.reddit.com/r/oraclecloud/comments/on2e25/resolving_oracle_cloud_out_of_capacity_issue_and/

[^6_11]: https://engineering.pipefy.com/2025/07/04/optimizing-kubernetes-costs-and-availability-in-oke-a-strategy-for-preemptible-nodes-and-descheduler-integration/

[^6_12]: https://www.youtube.com/watch?v=Xto9zROBwqY

[^6_13]: https://www.reddit.com/r/oraclecloud/comments/1f8pqsm/a_question_about_always_free_limits/

[^6_14]: https://docs.cloud.google.com/compute/docs/instances/preemptible

[^6_15]: https://docs.oracle.com/iaas/releasenotes/changes/21d76d43-267a-4bac-a3bb-9cff3af4eebf/index.htm

[^6_16]: https://www.reddit.com/r/selfhosted/comments/15q1o59/is_oracle_cloud_free_tier_actually_free_tier/

[^6_17]: https://www.linkedin.com/pulse/forgotten-ones-preemptible-burstable-instances-cost-saving-mahdjoubi-ibroe

[^6_18]: https://www.reddit.com/r/oraclecloud/comments/1otay98/oracle_cloud_reclaimed_my_always_free_arm/


---

# Initialization script

You can provide a startup script that runs when your instance boots up or restarts. Startup scripts can install software and updates, and ensure that services are running within the instance.
Choose cloud-init script file
Paste cloud-init script

Yes — use **Paste cloud-init script**. Cloud-init is the right place to do first-boot package installs, write config files, and enable services, and `runcmd` is the standard section for commands that should run after package setup and file writes are complete.[^7_1][^7_2][^7_3]

For your first pass, I recommend a **safe bootstrap script**, not a full “install AD4M from source and build everything on first boot” script. AD4M needs Node 18, pnpm, Deno, Rust, Go, and Holochain-related tooling, and that is enough moving parts that you want the instance to come up predictably first, then do the repo build by SSH once the machine is stable.[^7_4][^7_5]

## What to paste

Paste this as your cloud-init script:

```yaml
#cloud-config
package_update: true
package_upgrade: true

packages:
  - build-essential
  - git
  - curl
  - wget
  - unzip
  - zip
  - jq
  - ca-certificates
  - pkg-config
  - libssl-dev
  - libclang-dev
  - clang
  - cmake
  - make
  - ufw
  - fail2ban
  - htop
  - tmux
  - python3
  - python3-pip

users:
  - default
  - name: ad4m
    gecos: AD4M Service User
    shell: /bin/bash
    sudo: ALL=(ALL) NOPASSWD:ALL
    groups: sudo
    lock_passwd: true

write_files:
  - path: /etc/ssh/sshd_config.d/99-hardening.conf
    permissions: "0644"
    owner: root:root
    content: |
      PasswordAuthentication no
      PubkeyAuthentication yes
      PermitRootLogin no
      X11Forwarding no
      ClientAliveInterval 300
      ClientAliveCountMax 2

  - path: /usr/local/bin/ad4m-bootstrap.sh
    permissions: "0755"
    owner: root:root
    content: |
      #!/usr/bin/env bash
      set -euxo pipefail

      export DEBIAN_FRONTEND=noninteractive

      # Install Node.js 18
      curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
      apt-get install -y nodejs

      # Enable corepack for pnpm
      corepack enable || true
      corepack prepare pnpm@latest --activate || true

      # Install Rust for ad4m user
      sudo -u ad4m -H bash -lc 'curl https://sh.rustup.rs -sSf | sh -s -- -y'
      sudo -u ad4m -H bash -lc 'source ~/.cargo/env && rustup target add wasm32-unknown-unknown'

      # Install Deno for ad4m user
      sudo -u ad4m -H bash -lc 'curl -fsSL https://deno.land/install.sh | sh'

      # Install Go 1.21.x for ARM64
      ARCH="$(dpkg --print-architecture)"
      if [ "$ARCH" = "arm64" ]; then
        GO_TARBALL="go1.21.13.linux-arm64.tar.gz"
      else
        GO_TARBALL="go1.21.13.linux-amd64.tar.gz"
      fi

      cd /tmp
      wget -q "https://go.dev/dl/${GO_TARBALL}"
      rm -rf /usr/local/go
      tar -C /usr/local -xzf "${GO_TARBALL}"

      cat >/etc/profile.d/ad4m-paths.sh <<'EOF'
      export PATH=/usr/local/go/bin:$PATH
      export PATH=$HOME/.cargo/bin:$PATH
      export DENO_INSTALL=$HOME/.deno
      export PATH=$DENO_INSTALL/bin:$PATH
      EOF
      chmod 0644 /etc/profile.d/ad4m-paths.sh

      # Basic firewall: SSH only
      ufw allow OpenSSH
      yes | ufw enable || true

      # Enable fail2ban
      systemctl enable fail2ban
      systemctl restart fail2ban

      # Prepare workspace
      mkdir -p /opt/flossioullk
      chown ad4m:ad4m /opt/flossioullk

      # Marker file
      echo "bootstrap complete: $(date -Iseconds)" > /opt/flossioullk/bootstrap-complete.txt

runcmd:
  - systemctl daemon-reload
  - systemctl restart ssh || systemctl restart sshd || true
  - /usr/local/bin/ad4m-bootstrap.sh

final_message: "Cloud-init finished. Log in and continue AD4M install as user 'ad4m'."
```


## Why this version

This script does the reliable first-boot things:

- updates Ubuntu packages,[^7_2]
- installs the Linux build dependencies AD4M and Holochain-related Rust builds need, such as `build-essential`, `pkg-config`, and `libssl-dev`, which align with Holochain’s documented Linux prerequisites and the AD4M toolchain requirements.[^7_5][^7_4]
- installs Node 18, pnpm via Corepack, Rust with the WASM target, Deno, and Go 1.21 for ARM64, all of which AD4M’s repo says you need.[^7_5]
- hardens SSH and enables UFW with only SSH open, which matches your “local only first” plan.[^7_6]

What it **does not** do is automatically clone and build AD4M on boot. That is deliberate, because cloud-init is best used to get the machine into a good base state, while a large source build with multiple ecosystems is easier to debug interactively after the server is up.[^7_3][^7_2][^7_5]

## What you do after boot

After the instance comes up, SSH in and finish the repo install manually:

```bash
ssh -i /path/to/key ubuntu@YOUR_PUBLIC_IP
sudo su - ad4m
source /etc/profile.d/ad4m-paths.sh

git clone https://github.com/coasys/ad4m.git
cd ad4m
node -v
pnpm -v
deno --version
go version
rustc --version
```

Then follow the AD4M repo build flow. The README documents a full build path using `pnpm install`, then `cd core && pnpm install`, then `pnpm run build`, and also a lighter `pnpm run build-libs` option that skips bundling bootstrap languages and downloads them later if unchanged.[^7_5]

## One caution

This script installs the **general prerequisites**, but not the Holochain CLI itself. Holochain’s documentation shows installing the binaries with Cargo-based commands such as `cargo install --force holochain`, `holochain_cli`, and `lair_keystore`, but that part is still something I would run manually after login so you can see exactly what compiles and fails on your chosen image.[^7_4]

So the correct move in the Oracle UI is:

- choose **Paste cloud-init script**,[^7_1]
- paste the YAML above,
- launch the instance,
- wait for first boot to finish,
- then SSH in and continue the AD4M/Holochain install interactively.[^7_2][^7_5]

If you want, I can next give you the **post-boot terminal commands** in one clean copy-paste block for `ubuntu` and then `ad4m`.
<span style="display:none">[^7_10][^7_11][^7_12][^7_13][^7_14][^7_15][^7_16][^7_17][^7_7][^7_8][^7_9]</span>

<div align="center">⁂</div>

[^7_1]: https://www.youtube.com/watch?v=9DnCIpbn-8o

[^7_2]: https://oneuptime.com/blog/post/2026-03-02-how-to-run-scripts-at-first-boot-with-cloud-init-on-ubuntu/view

[^7_3]: https://stackoverflow.com/questions/50085873/create-systemd-unit-in-cloud-init-and-enable-it

[^7_4]: https://developer.holochain.org/get-started/install-without-nix/

[^7_5]: https://github.com/coasys/ad4m

[^7_6]: https://www.digitalocean.com/community/tutorials/ufw-essentials-common-firewall-rules-and-commands

[^7_7]: https://github.com/denoland/deno/issues/21516

[^7_8]: https://isograph.dev/docs/development-workflow/

[^7_9]: https://docs.deno.com/runtime/reference/cli/install/

[^7_10]: https://tinyhumans.gitbook.io/openhuman/developing/getting-set-up

[^7_11]: https://docs.snailycad.org/docs/guides/requirements/how-to-install-node-pnpm-npm-linux

[^7_12]: https://www.youtube.com/watch?v=J2fQQ70UHqo

[^7_13]: https://forums.oracle.com/ords/apexds/post/any-official-oracle-s-systemd-service-startup-script-to-run-4064

[^7_14]: https://pnpm.io/cli/approve-builds

[^7_15]: https://github.com/denoland/deno/discussions/30140

[^7_16]: https://next.nutanix.com/installation-configuration-23/ubuntu-20-04-autoinstall-using-cloud-init-custom-script-40713

[^7_17]: https://stackoverflow.com/questions/77383780/my-deno-app-cant-download-dependencies-on-my-ubuntu-22-04-server

