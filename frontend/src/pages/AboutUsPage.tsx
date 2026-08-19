import { Users } from "lucide-react";
import { PageHeader } from "../components/layout/PageHeader";
import { TeamPhoto } from "../components/cards/TeamPhoto";

export function AboutUsPage() {
  return (
    <div className="h-full overflow-y-auto pb-8">
      <PageHeader
        title="Our Story"
        subtitle="How this dashboard came to be"
        icon={<Users size={20} strokeWidth={2.25} />}
      />

      <div className="mx-auto max-w-3xl space-y-8 text-[15px] leading-relaxed text-text-primary">
        <section className="space-y-3">
          <p className="text-text-secondary">
            The three of us joined the University of Windsor as Mitacs GRA students, working under
            host supervisor Dr. Shanthi Johnson and with support from Dr. Parthiban Natarajan,
            Initiatives Officer at UWindsor's Office of the Vice-President, Research and Innovation
            (VPRI), along with home supervisor Dr. D Rajeswari.
          </p>
          <p className="text-text-secondary">
            Our project was to build an app to help seniors across Canada cope with social
            isolation, grounded in data on the Age-Friendly University movement — fitting, since
            UWindsor is itself a designated Age-Friendly University. But the underlying data turned
            out to be scattered across inconsistent pages and painful to work with directly. So we
            shifted focus: instead of shipping an app on top of data nobody could actually use, we
            built the dashboard you're looking at now — the tool we needed just to make sense of
            that data in the first place.
          </p>
          <p className="font-medium text-text-primary">Turns out other people needed this too.</p>
        </section>

        <section className="space-y-4">
          <h3 className="text-lg font-bold text-text-primary">The team</h3>
          <div className="grid grid-cols-1 gap-6 py-2 sm:grid-cols-3">
            <TeamPhoto
              src="/team/dron.jpg"
              name="Dron Haritwal"
              linkedin="https://www.linkedin.com/in/dronharitwal"
            />
            <TeamPhoto
              src="/team/amala.png"
              name="Amala K J"
              linkedin="https://www.linkedin.com/in/amala-k-j-3b7666144/"
            />
            <TeamPhoto
              src="/team/apurva.jpg"
              name="Apurva Shovit"
              linkedin="https://www.linkedin.com/in/apurva-shovit-541ba2281/"
            />
          </div>
        </section>

        <section className="space-y-4">
          <h3 className="text-lg font-bold text-text-primary">Our supervisors</h3>
          <p className="text-text-secondary">
            Thanks to the mentors who guided this project from the start:
          </p>
          <div className="grid grid-cols-1 gap-6 py-2 sm:grid-cols-3">
            <TeamPhoto
              src="/team/johnson.jpg"
              name="Dr. Shanthi Johnson"
              role="Host Supervisor"
              linkedin="https://www.linkedin.com/in/shanthi-johnson-533b1110/"
            />
            <TeamPhoto
              src="/team/parthiban.jpg"
              name="Dr. Parthiban Natarajan"
              role="Initiatives Officer, VPRI"
              linkedin="https://www.linkedin.com/in/parthiban-natarajan/"
            />
            <TeamPhoto
              src="/team/rajeswari.jpg"
              name="Dr. D Rajeswari"
              role="Home Supervisor"
              linkedin="https://www.linkedin.com/in/rajeswaridevarajan/"
            />
          </div>
        </section>

        <section className="space-y-2">
          <h3 className="text-lg font-bold text-text-primary">Contact</h3>
          <p className="text-text-secondary">
            Found a bug? Have an idea for something we should add? We'd love to hear from you —
            reach out to Dron on{" "}
            <a
              href="https://www.linkedin.com/in/dronharitwal"
              target="_blank"
              rel="noopener noreferrer"
              className="font-medium text-ink-terracotta underline-offset-2 hover:underline"
            >
              LinkedIn
            </a>
            .
          </p>
        </section>
      </div>
    </div>
  );
}
