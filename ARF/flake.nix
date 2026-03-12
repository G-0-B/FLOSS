{
  description = "FLOSSIOULLK Rose Forest – Holochain hApp dev environment";

  inputs = {
    holonix = {
      url = "github:holochain/holonix?ref=main";
      flake = true;
    };
    nixpkgs.follows = "holonix/nixpkgs";
  };

  outputs = inputs @ { holonix, nixpkgs, ... }:
    holonix.inputs.flake-parts.lib.mkFlake { inherit inputs; } {
      systems = builtins.attrNames holonix.devShells;

      perSystem = { system, pkgs, ... }: {
        devShells.default = pkgs.mkShell {
          inputsFrom = [ holonix.devShells.${system}.default ];
          packages = with pkgs; [
            nodejs_20
          ];

          shellHook = ''
            echo "FLOSSIOULLK Rose Forest dev shell"
            echo "  holochain: $(holochain --version 2>/dev/null || echo 'not found')"
            echo "  hc:        $(hc --version 2>/dev/null || echo 'not found')"
            echo "  rustc:     $(rustc --version)"
            echo ""
            echo "Build:  cargo build --release --target wasm32-unknown-unknown"
            echo "Pack:   hc dna pack dnas/rose_forest/workdir/"
            echo "        hc app pack workdir/"
            echo "Test:   cd tests/tryorama && npm test"
          '';
        };
      };
    };
}
