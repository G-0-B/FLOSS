export type TruthStatus = "verified" | "specified";

export type EvidencePath = {
  readonly path: string;
  readonly truth_status: "verified";
};

export type ManifestLink = EvidencePath & {
  readonly label: string;
  readonly description: string;
  readonly href: string;
};

export type CommonsManifest = {
  readonly name: string;
  readonly project: string;
  readonly expanded_name: string;
  readonly truth_status: TruthStatus;
  readonly purpose: {
    readonly statement: string;
    readonly truth_status: TruthStatus;
  };
  readonly authority: {
    readonly principle: string;
    readonly principle_truth_status: "verified";
    readonly evidence: readonly EvidencePath[];
    readonly worker_role: string;
    readonly truth_status: "specified";
    readonly not_authority: readonly string[];
  };
  readonly links: readonly ManifestLink[];
  readonly mediums: readonly string[];
  readonly privacy: {
    readonly read_only: true;
    readonly stores_user_data: false;
    readonly uses_cookies: false;
    readonly truth_status: "specified";
  };
};

export const commonsManifest: CommonsManifest = {
  name: "FLOSSI0ULLK Public Commons Gateway",
  project: "FLOSSI0ULLK",
  expanded_name:
    "Free Libre Open Source Singularity of Infinite Overflowing Unconditional Love, Light, and Knowledge",
  truth_status: "specified",
  purpose: {
    statement:
      "A public, read-only orientation gateway into the FLOSSI0ULLK research commons.",
    truth_status: "specified"
  },
  authority: {
    principle: "Logic validates, neural assists.",
    principle_truth_status: "verified",
    evidence: [
      { path: "INDEX.md", truth_status: "verified" },
      { path: "FLOSS/CLAUDE.md", truth_status: "verified" },
      {
        path: "FLOSS/docs/specs/provenance-packet.spec.md",
        truth_status: "verified"
      }
    ],
    worker_role: "public read-only orientation gateway",
    truth_status: "specified",
    not_authority: [
      "canonical truth",
      "consensus decision",
      "Holochain validation",
      "consent decision",
      "governed write intake"
    ]
  },
  links: [
    {
      label: "Project index",
      description: "Repository map and canonical document registry.",
      href: "https://github.com/G-0-B/FLOSS/blob/main/INDEX.md",
      path: "INDEX.md",
      truth_status: "verified"
    },
    {
      label: "Project orientation",
      description: "Current agent-facing operating notes for FLOSS.",
      href: "https://github.com/G-0-B/FLOSS/blob/main/FLOSS/CLAUDE.md",
      path: "FLOSS/CLAUDE.md",
      truth_status: "verified"
    },
    {
      label: "Gateway design spec",
      description: "Design boundary for this first Worker slice.",
      href: "https://github.com/G-0-B/FLOSS/blob/main/FLOSS/docs/superpowers/specs/2026-06-16-cloudflare-commons-gateway-design.md",
      path: "FLOSS/docs/superpowers/specs/2026-06-16-cloudflare-commons-gateway-design.md",
      truth_status: "verified"
    }
  ],
  mediums: ["web", "json", "open-source repository"],
  privacy: {
    read_only: true,
    stores_user_data: false,
    uses_cookies: false,
    truth_status: "specified"
  }
};

export const healthPayload = {
  status: "ok",
  service: commonsManifest.name,
  read_only: true,
  authority: commonsManifest.authority.worker_role
} as const;
