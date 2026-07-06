/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  transpilePackages: ["@lexflow/ui", "@lexflow/shared"],
};

export default nextConfig;
