import { Users } from "lucide-react";
import { PageHeader } from "../components/layout/PageHeader";
import { TeamPhoto } from "../components/cards/TeamPhoto";

export function AboutUsPage() {
  return (
    <div className="h-full overflow-y-auto pb-8">
      <PageHeader
        title="About Us"
        subtitle="How this dashboard came to be"
        icon={<Users size={20} strokeWidth={2.25} />}
      />

      <div className="mx-auto max-w-3xl space-y-8 text-[15px] leading-relaxed text-text-primary">
        <section className="space-y-3">
          <h3 className="text-lg font-bold text-text-primary">Our story</h3>
          <p className="text-text-secondary">
            This started as three of us getting fed up with a spreadsheet. We kept going back to the
            Age-Friendly University Global Network's member page for our own work, and every time we
            needed a simple answer — how many members in a region, how a principle was actually
            being applied — we ended up scrolling and counting by hand.
          </p>
          <p className="text-text-secondary">
            So one weekend we just built the thing we wished existed. It was rough at first, but it
            worked well enough that we kept reaching for it ourselves, and then friends started
            asking to borrow it too. That's when we figured it was worth cleaning up and putting out
            in the open.
          </p>
          <p className="font-medium text-text-primary">Turns out other people needed this too.</p>
        </section>

        <section className="space-y-4">
          <h3 className="text-lg font-bold text-text-primary">About us</h3>
          <div className="grid grid-cols-1 gap-6 py-2 sm:grid-cols-3">
            <TeamPhoto
              src="/team/dron.jpg"
              name="Dron Haritwal"
              role="Windsor, ON"
              linkedin="https://www.linkedin.com/in/dronharitwal"
            />
            <TeamPhoto src="/team/amala.png" name="Amala K J" role="Windsor, ON" />
            <TeamPhoto
              src="/team/apurva.jpg"
              name="Apurva Shovit"
              role="Windsor, ON"
              linkedin="https://www.linkedin.com/in/apurva-shovit-541ba2281/"
            />
          </div>
        </section>

        <section className="space-y-2">
          <p className="text-text-secondary">
            We'd also like to say thanks to someone who's been in our corner from the start:
          </p>
          <p className="text-text-primary">
            <strong className="font-semibold">Dr. Shanthi Johnson</strong>{" "}
            <span className="text-text-secondary">— for the guidance and the room to run with it.</span>
          </p>
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
