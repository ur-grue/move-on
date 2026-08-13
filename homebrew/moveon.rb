class Moveon < Formula
  include Language::Python::Virtualenv

  desc "Extract your AI provider data. Request deletion. Move on."
  homepage "https://github.com/ur-grue/move-on"
  url "https://github.com/ur-grue/move-on/archive/refs/tags/v1.0.0.tar.gz"
  sha256 "d7126a02814043553a8882b559259333a5d861c2b6b8895dde9de8cdc9a3eb71"
  license "MIT"

  depends_on "python@3.13"

  resource "typer" do
    url "https://files.pythonhosted.org/packages/ae/40/4a3db7990d1f62a53182aa96eaef57aeb2886a27f90a195bc66713565d31/typer-0.27.1.tar.gz"
    sha256 "a79bef8469a79c45498e7b814ecf8d603cc7644e9acbd9e19cac0334240b18df"
  end

  resource "pydantic" do
    url "https://files.pythonhosted.org/packages/18/a5/b60d21ac674192f8ab0ba4e9fd860690f9b4a6e51ca5df118733b487d8d6/pydantic-2.13.4.tar.gz"
    sha256 "c40756b57adaa8b1efeeced5c196f3f3b7c435f90e84ea7f443901bec8099ef6"
  end

  resource "pydantic-core" do
    url "https://files.pythonhosted.org/packages/26/1b/34440c0294cbc90e57873cbc28465a7e6d6216984cf3ce195cb8ca6791ee/pydantic_core-2.48.0.tar.gz"
    sha256 "8714f70dafdffea0a5596cc88eddbdc71f5856563947970dcbd0f1ced61ed05f"
  end

  resource "click" do
    url "https://files.pythonhosted.org/packages/76/d4/81420972a676e8ffea40450d8c8c92943e7218a78fe9b64359836cc9876b/click-8.4.2.tar.gz"
    sha256 "9a6cea6e60b17ebe0a44c5cc636d94f09bd66142c1cd7d8b4cd731c4917a15f6"
  end

  resource "typing-extensions" do
    url "https://files.pythonhosted.org/packages/f6/cc/6253133b5bb138fc3306cebfbda2c520f545d36b5be2c7255cc528bb45d6/typing_extensions-4.16.0.tar.gz"
    sha256 "dc983d19a509c94dba722ee6abd33940f7c05a89e243c47e907eb4db6f1a43e5"
  end

  resource "annotated-types" do
    url "https://files.pythonhosted.org/packages/5f/56/a8120250d128bed162cd73c76d45f6ef9991f3e068f62a8ee060afa3104a/annotated_types-0.8.0.tar.gz"
    sha256 "13b2beaad985e05e2d6407ee4c4f35590b11f8d693a258a561055cac8f64cab7"
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
