using CalmCadence.Core.Enums;
using CalmCadence.Core.Models;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace CalmCadence.Data.Configurations;

public class HabitConfiguration : IEntityTypeConfiguration<Habit>
{
    public void Configure(EntityTypeBuilder<Habit> builder)
    {
        builder.ToTable("Habits");
        builder.HasKey(h => h.Id);

        builder.Property(h => h.Name).IsRequired().HasMaxLength(200);
        builder.Property(h => h.Description).HasMaxLength(2000);
        builder.Property(h => h.Type).HasConversion<int>();
        builder.Property(h => h.ColorHex).HasMaxLength(9);
        builder.Property(h => h.ScheduleJson).HasMaxLength(4000);
        builder.Property(h => h.CreatedAt).IsRequired();

        builder.HasMany(h => h.Logs)
               .WithOne(l => l.Habit)
               .HasForeignKey(l => l.HabitId)
               .OnDelete(DeleteBehavior.Cascade);

        builder.HasIndex(h => new { h.Type, h.IsArchived });
    }
}
