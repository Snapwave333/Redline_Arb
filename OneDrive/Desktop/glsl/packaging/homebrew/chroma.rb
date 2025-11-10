class Chroma < Formula
  desc "Rust-based ASCII art shader audio visualizer for your terminal"
  homepage "https://github.com/yuri-xyz/chroma"
  url "https://github.com/yuri-xyz/chroma/archive/v0.2.0.tar.gz"
  sha256 "" # Will be calculated after release
  license "GPL-3.0-or-later"
  head "https://github.com/yuri-xyz/chroma.git", branch: "master"

  depends_on "rust" => :build

  def install
    system "cargo", "install", "--locked", "--root", prefix, "--path", "."
  end

  test do
    # Test that the binary runs and shows version
    assert_match "chroma", shell_output("#{bin}/chroma --help", 1)
  end
end
