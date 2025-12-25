import { Header } from "@/components/sections/header";
import { Hero } from "@/components/sections/hero";
import { Problems } from "@/components/sections/problems";
import { Features } from "@/components/sections/features";
import { HowItWorks } from "@/components/sections/how-it-works";
import { Comparison } from "@/components/sections/comparison";
import { Pricing } from "@/components/sections/pricing";
import { FAQ } from "@/components/sections/faq";
import { Footer } from "@/components/sections/footer";

export default function Home() {
  return (
    <>
      <Header />
      <main>
        <Hero />
        <Problems />
        <Features />
        <HowItWorks />
        <Comparison />
        <Pricing />
        <FAQ />
      </main>
      <Footer />
    </>
  );
}
