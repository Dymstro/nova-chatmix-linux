{
  description = "steelseries chatmix support for linux";
  inputs = { nixpkgs.url = "github:nixos/nixpkgs/nixos-24.11"; };

  outputs = { self, nixpkgs, ... }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      lib = nixpkgs.lib;
    in {
      packages.${system} = let pkgs = nixpkgs.legacyPackages.${system};
      in {
        default = pkgs.python3Packages.buildPythonApplication {
          pname = "nova-chatmix";
          version = "1.0";

          propagatedBuildInputs =
            [ pkgs.python3Packages.pyusb pkgs.pulseaudio pkgs.pipewire ];

          src = ./.;

          postInstall = ''
            mkdir -p $out/etc/udev/rules.d
            cp ./50-nova-pro-wireless.rules $out/etc/udev/rules.d/
          '';

          meta = {
            homepage = "https://git.dymstro.nl/Dymstro/nova-chatmix-linux";
            description =
              "ChatMix for the Steelseries Arctis Nova Pro Wireless";
            license = lib.licenses.bsd0;
          };
        };
      };
      devShell = pkgs.mkShell {
        buildInputs = with pkgs; [ python3 python3Packages.pyusb ];
      };
      nixosModule = { config, lib, pkgs, ... }: {
        options.services.nova-chatmix = {
          enable = lib.mkEnableOption "steelseries chatmix support";
        };
        config = lib.mkIf config.services.nova-chatmix.enable {
          services.udev.packages = [ self.packages.${system}.default ];
          systemd.user.services.nova-chatmix = {
            enable = true;
            after = [ "pipewire.service" "pipewire-pulse.service" ];
            wantedBy = [ "default.target" ];
            wants = [ "network-online.target" ];
            description =
              "This will enable ChatMix for the Steelseries Arctis Nova Pro Wireless";
            serviceConfig = {
              Type = "simple";
              Restart = "always";
              ExecStartPre = "${pkgs.coreutils-full}/bin/sleep 1";
              ExecStart = "${self.packages.${system}.default}/bin/nova.py";
            };
          };
        };
      };
    };
}
