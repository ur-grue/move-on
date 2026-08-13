class Moveon < Formula
  include Language::Python::Virtualenv

  desc "Extract your AI provider data. Request deletion. Move on."
  homepage "https://github.com/ur-grue/move-on"
  url "https://github.com/ur-grue/move-on/archive/refs/tags/v1.0.0.tar.gz"
  sha256 "d7126a02814043553a8882b559259333a5d861c2b6b8895dde9de8cdc9a3eb71"
  license "MIT"

  depends_on "python@3.13"

  resource "typer" do
    url "https://files.pythonhosted.org/packages/eb/1e/25adfd4b0ee22e0c33395246e44b75d82b0e282ae80e3e9c1af5db7a77c8/typer-0.15.4.tar.gz"
    sha256 "89507b1047af7e00e89e08e7e42de0b7d2704c88dee3cb4a1e0266d7f37ade04"
  end

  resource "pydantic" do
    url "https://files.pythonhosted.org/packages/21/06/efe0e703aecd28e2e3d433b3af2a53f92208e32530a4e73f5ddd10b05f87/pydantic-2.11.7.tar.gz"
    sha256 "d989c4310e8e50397bddbe886f5e4d409d72ed128e45e0e68ae3e6a550e7984b"
  end

  resource "pydantic-core" do
    url "https://files.pythonhosted.org/packages/ad/88/5f5c1f2e4e4ee68f27f2c2878e3fd2f57374e9c3b6bfc873a0d4ad85a5ca/pydantic_core-2.33.2.tar.gz"
    sha256 "7cb8bc3605c29176e1b105350d2e6474142d7c1bd1d9327c4a9bdb46bf827acc"
  end

  resource "click" do
    url "https://files.pythonhosted.org/packages/b9/2e/0090cbf739cee7d23781ad4b89a9894a41538e4fcf4c31dcdd705b78eb8b/click-8.1.8.tar.gz"
    sha256 "ed53c9d8990d83c2a27deae68e4ee337473f6330c040a31d4225c9574d0c3e71"
  end

  resource "typing-extensions" do
    url "https://files.pythonhosted.org/packages/f6/37/23083fcd6e35492f9f5b0e6c32217698c9e6e2bf9268e2e4e39050a07da7/typing_extensions-4.14.0.tar.gz"
    sha256 "8676b788e32f02ab42d9e7c61324048ae4c6d844a399eebace3d4979d75ceef4"
  end

  resource "annotated-types" do
    url "https://files.pythonhosted.org/packages/ee/67/531ea369ba64dcff5ec9c3402f9f51bf748cec26dde048a2f973a4eea7f5/annotated_types-0.7.0.tar.gz"
    sha256 "aff07c09a53a08bc8cfccb9c85b05f1aa9a2a6f23728d790723543408344ce89"
  end

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match "moveon #{version}", shell_output("#{bin}/moveon --version")
    assert_match "openai", shell_output("#{bin}/moveon guide")
    assert_match "xai", shell_output("#{bin}/moveon guide")
    assert_match "perplexity", shell_output("#{bin}/moveon guide")
    assert_match "track", shell_output("#{bin}/moveon --help")
    assert_match "escalate", shell_output("#{bin}/moveon --help")
  end
end
