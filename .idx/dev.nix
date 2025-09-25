# To learn more about how to use Nix to configure your environment
# see: https://firebase.google.com/docs/studio/customize-workspace
{ pkgs, ... }: {
  # Which nixpkgs channel to use.
  channel = "stable-24.05"; # or "unstable"

  # Use https://search.nixos.org/packages to find packages
  packages = [
    # pkgs.go
    # pkgs.python311
    # pkgs.python311Packages.pip
    # pkgs.nodejs_20
    # pkgs.nodePackages.nodemon
  ];

  # Sets environment variables in the workspace
  env = {};
  idx = {
    # Search for the extensions you want on https://open-vsx.org/ and use "publisher.id"
    extensions = [
      # "username.extension-name"
    ];

    # Enable previews and customize configuration
    previews = {
      enable = true;
      previews = [
        # {
        #   # Command to start the process
        #   command = ["npm", "run", "dev", "--", "--port", "$PORT"];
        #   # Display name for the tab
        #   label = "Web";
        #   # Port to expose on the container
        #   port = 3000;
        # }
      ];
    };

    # Specify the path to a file to open on startup
    # startup = {
    #   openFile = "README.md";
    # };
  };
}
